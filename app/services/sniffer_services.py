from urllib.parse import urlparse
from app.models.schemas import LendersExtractSchema
from app.utils.prompts import (
    lenders_data_prompt, lenders_data_system_message
)
from app.services.llm_services import openai_analyzer
from app.services.webpage import (
    extract_webpage_content, extract_urls_from_website, 
    filter_urls_by_keywords, normalize_urls, extract_content_from_url
)

################################# Lenders Data Service Functions ####################################
# 1. Lenders data based on the custom method
def get_lenders_data(url: str, multiple_urls: list[str] = None, keywords: list[str] = None) -> dict:

    # a. Extract the urls from the website
    urls = extract_urls_from_website(url)
    try:
        domain = f"https://{urlparse(url).netloc}"
    except Exception as e:
        print(f"❌ Error parsing url: {e}")
        

    # b. Filter the urls by keywords
    filtered_urls = filter_urls_by_keywords(urls.get("hrefs", []), keywords)
    print("FILTERED URLS: ", filtered_urls)
    print("DOMAIN:------------------ ", domain)

    if multiple_urls:
        filtered_urls = filtered_urls + multiple_urls

    # c. Normalize the urls
    normalized_urls = normalize_urls(filtered_urls, domain)
    print("NORMALIZED URLS: ", normalized_urls)

    # d. Extract the content from the urls
    extracted_data = {}
    successful_extractions = 0
    failed_extractions = 0

    filtered_urls = list(set(normalized_urls))
    for url in filtered_urls:
        try:
            text = extract_content_from_url(url, domain=domain)
            if text and len(text.strip()) > 0:
                extracted_data[url] = text
                successful_extractions += 1
        except Exception as e:
            failed_extractions += 1
            print(f"❌ Error scraping {url}: {e}")

    # e. Flatten and de-duplicate data
    final_data = []
    total_lines_processed = 0
    
    for url, value in extracted_data.items():
        lines = value.split("\n")
        total_lines_processed += len(lines)
        for line in lines:
            cleaned = line.strip()
            if cleaned and cleaned not in final_data:
                final_data.append(cleaned)
    
    final_data = ", ".join(final_data)
    print(f"📄 Total processed data: {len(final_data)} characters")

    if not final_data:
        print("⚠️ No usable data extracted after cleaning. Skipping.")
        return ""

    # Prepare and call GPT model
    cleaned_data = final_data.replace("{", "(").replace("}", ")")
    
    # Data for prompt
    system_message = lenders_data_system_message
    prompt = lenders_data_prompt.format(lender_name="IDBI Bank", final_data=cleaned_data)  # TODO: Add the lender name
    primary_model_response, primary_token_usage = openai_analyzer.gpt_model_structured_response(
        system_message,
        prompt,
        model="gpt-4.1-mini-2025-04-14",
        response_format=LendersExtractSchema
        )
    
    # Primary Model Parsed Response
    parsed_response = primary_model_response.choices[0].message.content

    # Check if the response is valid

    return {
        "data": parsed_response.get("output", []), 
        "successful_extractions": successful_extractions, 
        "failed_extractions": failed_extractions
        }
