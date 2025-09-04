import requests
import io
import re
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import pandas as pd
# import openpyxl

from PyPDF2 import PdfReader
# from docx import Document
# import textract
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from prompts import prompt, system_message, search_system_message
from supabase import create_client, Client
from datetime import datetime
import pytz

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_TABLE:
    raise ValueError("Missing Supabase environment variables. Please check your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✅ Supabase client initialized with URL: {SUPABASE_URL}")
    print(f"📋 Table name: {SUPABASE_TABLE}")
except Exception as e:
    print(f"❌ Error initializing Supabase client: {e}")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "Key: None")
    raise

# Set timezone (e.g., Asia/Kolkata, UTC, US/Eastern)
timezone = pytz.timezone('Asia/Kolkata')


# Keywords to filter urls
keywords = ["interest","roi","mitc","term","condition","approved", "foir", "ltv", "lap", "home",
"roi", "house","salaried","employed","credit score","score","profession","borrower", "criteria","eligibility",
"property type"]

key_prompt_map = {
    "lender_type": "Is the lender a public sector bank, private bank, NBFC, or HFC?",
    "foir": "General FOIR (Fixed Obligation to Income Ratio) required for home loan eligibility",
    "foir_salaried": "FOIR requirement specifically for salaried individuals",
    "foir_selfsalaried": "FOIR requirement specifically for self-employed applicants",
    "homeloan_roi": "Current home loan interest rate (ROI) offered by the lender",
    "lap_roi": "Interest rate for Loan Against Property (LAP)",
    "homeloan_ltv": "Loan-to-value ratio allowed for home loans",
    "lap_ltv": "Loan-to-value ratio allowed for LAP",
    "list_of_documents": "List of documents required to apply for a home loan",
    "minimum_co_borrower_income": "Minimum income required from a co-borrower, if applicable",
    "minimum_credit_score": "Minimum credit score required to be eligible for a home loan",
    "remarks": "Any additional remarks or special conditions for home loan products",
    "accepted_agreement_type": "Types of property agreements accepted (e.g., Registered Sale Deed, Allotment Letter)",
    "accepted_usage_type": "Accepted usage types for the financed property (e.g., Residential, Self-occupied, Rental)",
    "mitc": "URL or details of the Most Important Terms and Conditions (MITC)",
    "loan_products": "Different home loan or LAP products offered by the lender",
    "target_customers": "Target customer segments for the home loan (e.g., salaried, NRI, women)",
    "eligibility_criteria": "Detailed eligibility conditions for home loan applicants",
    "eligible_profession_type": "Types of professions eligible for the loan (e.g., salaried, self-employed)",
    "key_features": "Key features and benefits of the home loan product",
    "special_offers_available": "Any special offers, discounts, or schemes currently available",
    "customer_support_contact_numbers": "Customer care or support contact numbers for loan-related queries",
    "loan_approval_time": "Average time taken to approve a home loan application",
    "processing_time": "Time taken for overall loan processing including disbursement",
    "minimum_loan_amount": "Minimum loan amount offered",
    "maximum_loan_amount": "Maximum loan amount available",
    "loan_tenure_range": "Minimum and maximum tenure range for the loan",
    "primary_borrower_income_range": "Income range required for the primary borrower",
    "co_borrower_income_range": "Income range required for the co-borrower",
    "processing_fees": "Processing fee applicable on the loan",
    "pre_payment_charges": "Prepayment charges, if any, applicable on the loan",
    "fore_closure_charges": "Foreclosure charges, if any, for closing the loan before tenure ends",
    "approved_property_types": "Types of properties approved for financing by the lender",
    "property_type_specifications": "Specific requirements or conditions on property types (e.g., freehold, RERA approved)",
}



# def load_input_data(data_path):
#     input_data = pd.read_excel(data_path, sheet_name="Sheet1")
#     return input_data

def extract_base_url(full_url):
    parsed = urlparse(full_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    return base_url


def clean_model_response(text: str) -> str:
    """
    Removes markdown-style links and URLs inside parentheses or square brackets.
    """
    # Remove markdown-style links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove any standalone URLs in parentheses (e.g., (https://...))
    text = re.sub(r'\(https?://[^\s)]+\)', '', text)

    # Remove square bracket citations like [source]
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s{2,}', ' ', text).strip()

    return text


def normalize_urls(raw_urls, base_domain):
    valid_urls = []
    base_domain = base_domain.rstrip('/')  # Ensure no trailing slash

    for url in raw_urls:
        url = url.strip()

        parsed = urlparse(url)

        # If scheme and netloc are missing, treat it as relative
        if not parsed.scheme or not parsed.netloc:
            full_url = urljoin(base_domain + '/', url)
            valid_urls.append(full_url)
        else:
            valid_urls.append(url)

    return valid_urls



def extract_urls_from_website(homeloan_website):
    response = requests.get(homeloan_website, timeout=15)
    response.raise_for_status()
    content = response.content
    soup = BeautifulSoup(response.text, 'html.parser')
    # Step 1: Extract all <a href="..."> links
    hrefs = [a['href'] for a in soup.find_all('a', href=True)]

    # Step 2: Extract all <p> paragraph text
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

    return {"hrefs":hrefs,"paragraphs":paragraphs}




def filter_urls_by_keywords(urls, domain, keywords):
    matched_urls = []
    domain = domain.lower()
    keywords = [k.lower() for k in keywords]

    for url in urls:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()

        # Only match the path+query, not the domain
        searchable_text = path + ' ' + parsed.query

        if any(keyword in searchable_text for keyword in keywords):
            matched_urls.append(url)

    return matched_urls





# Supported extensions and their handlers
def extract_content_from_url(url,domain):
    if not url.startswith("http"):
        url = domain +"/"+ url
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.content

        # Determine file extension
        path = urlparse(url).path
        extension = path.split('.')[-1].lower()

        if extension == 'pdf':
            with io.BytesIO(content) as f:
                reader = PdfReader(f)
                return '\n'.join([page.extract_text() or '' for page in reader.pages])

        # elif extension == 'docx':
        #     with io.BytesIO(content) as f:
        #         doc = Document(f)
        #         return '\n'.join([para.text for para in doc.paragraphs])

        # elif extension == 'doc':
        #     with io.BytesIO(content) as f:
        #         text = textract.process('', input_stream=f)
        #         return text.decode('utf-8', errors='ignore')

        elif extension in ['xls', 'xlsx']:
            with io.BytesIO(content) as f:
                df = pd.read_excel(f, dtype=str)
                return df.to_string(index=False)

        # elif extension in ['ppt', 'pptx']:
        #     with io.BytesIO(content) as f:
        #         text = textract.process('', input_stream=f)
        #         return text.decode('utf-8', errors='ignore')

        elif extension == 'csv':
            with io.BytesIO(content) as f:
                df = pd.read_csv(f, dtype=str)
                return df.to_string(index=False)

        elif extension == 'txt':
            return content.decode('utf-8', errors='ignore')

        elif extension in ['html', 'htm'] or '.' not in path:
            # Handle normal HTML pages or URLs with no extension
            soup = BeautifulSoup(response.text, 'html.parser')
            # Step 1: Extract all <a href="..."> links
            hrefs = [a['href'] for a in soup.find_all('a', href=True)]

            # Step 2: Extract all <p> paragraph text
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

            # Step 3: Remove script/style tags and extract clean visible text
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            visible_text = soup.get_text(separator='\n')
            visible_text_lines = [line.strip() for line in visible_text.splitlines()]
            visible_text_cleaned = '\n'.join(line for line in visible_text_lines if line)

            return visible_text_cleaned

        else:
            return f"[Unsupported file type: .{extension}]"

    except Exception as e:
        return f"❌ Error processing {url}: {e}"



# Function to send a prompt to GPT model
def gpt_model_response(prompt, model="gpt-4.1-mini-2025-04-14"):
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # creativity
        )
        return response
    except Exception as e:
        return f"Error: {e}"


def gpt_search_response(search_prompt, model="gpt-4o-mini-search-preview-2025-03-11"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": search_system_message},
             {"role": "user", "content": search_prompt}],
        )
        return response
    except Exception as e:
        return f"Error: {e}"


    
# def update_excel_row(workbook_path, target_row, json_data):

#     # Load the Excel workbook
#     wb = openpyxl.load_workbook(workbook_path)

#     # Select the sheet
#     sheet = wb['Sheet1']  # Or wb.active

#     # Target row number (1-based index)
#     target_row = target_row + 1

#     # New data to update the row
#     column_headers  = ["alias","official_website","homeloan_website","lender_type",	"foir",	"foir_salaried",	"foir_selfsalaried",	"homeloan_roi",	"lap_roi",
#     	"homeloan_ltv",	"lap_ltv",	"list_of_documents",	"minimum_co_borrower_income",	"minimum_credit_score",
#         "remarks",	"accepted_agreement_type",	"accepted_usage_type",	"mitc",	"loan_products",	"target_customers",
#         "eligibility_criteria",	"eligible_profession_type",	"key_features",	"special_offers_available",
#         "customer_support_contact_numbers",	"loan_approval_time",	"processing_time",	"minimum_loan_amount",
#         "maximum_loan_amount",	"loan_tenure_range", "primary_borrower_income_range", "co_borrower_income_range",
#         "processing_fees",	"pre_payment_charges",	"fore_closure_charges",	"approved_property_types",	
#         "property_type_specifications",	"source_urls","updated_at"]

#     for col_index, header in enumerate(column_headers, start=4):
#         value = json_data.get(header, "")  # Default to empty string if key not found

#         # Convert unsupported types to string
#         if isinstance(value, (dict, list)):
#             value = str(value)
#         elif value is None:
#             value = ""

#         sheet.cell(row=target_row, column=col_index, value=value)

#     # Save the workbook
#     wb.save(workbook_path)
#     print(f"✅ Row {target_row} updated in {workbook_path}")




    # Supabase Database Functions

def fetch_all_rows(query):
    """
    Fetch all rows from Supabase table using a query.
    Note: For Supabase, we'll use the table name and filters instead of raw SQL.
    """
    try:
        # Parse the query to extract table name and conditions
        if "where" in query.lower():
            # Extract table name and conditions
            table_match = query.lower().split("from")[1].split("where")[0].strip()
            table_name = table_match.split()[0] if table_match else SUPABASE_TABLE
            
            # Extract conditions after WHERE
            where_clause = query.lower().split("where")[1].strip()
            
            # Handle specific conditions
            if "updated_at is null" in where_clause.lower():
                print("Fetching lenders with null updated_at")
                # Get both NULL and empty values
                null_response = supabase.table(table_name).select("*").is_("updated_at", "null").execute()
                empty_response = supabase.table(table_name).select("*").eq("updated_at", "").execute()
                response_data = null_response.data + empty_response.data
                response_data.sort(key=lambda x: x.get('lender', ''))
                return response_data
            elif "updated_at is not null" in where_clause.lower():
                print("Fetching lenders with not null updated_at")
                # Get rows that are not NULL and not empty
                response = supabase.table(table_name).select("*").not_.is_("updated_at", "null").neq("updated_at", "").execute()
            else:
                print("Fetching all lenders")
                # For other conditions, fetch all and filter in Python
                response = supabase.table(table_name).select("*").execute()
                # You can add more specific filtering logic here
                
            return response.data
        else:
            print("Fetching all lenders-------else condition.")
            # Simple SELECT * FROM table
            table_name = query.lower().split("from")[1].strip().split()[0] if "from" in query.lower() else SUPABASE_TABLE
            response = supabase.table(table_name).select("*").execute()
            return response.data
            
    except Exception as e:
        print(f"❌ Error fetching rows: {e}")
        return []

def fetch_lenders_with_null_updated_at():
    """
    Fetch all lenders where updated_at is null or empty, ordered by lender name.
    """
    try:
        print(f"🔍 Fetching lenders from table: {SUPABASE_TABLE}")
        
        # First, get rows where updated_at is NULL
        null_response = supabase.table(SUPABASE_TABLE).select("*").is_("updated_at", "null").execute()
        print(f"📊 Found {len(null_response.data)} rows with NULL updated_at")
        
        # Then, get rows where updated_at is empty string
        empty_response = supabase.table(SUPABASE_TABLE).select("*").eq("updated_at", "").execute()
        print(f"📊 Found {len(empty_response.data)} rows with empty updated_at")
        
        # Combine both results
        all_data = null_response.data + empty_response.data
        
        # Sort by lender name
        all_data.sort(key=lambda x: x.get('lender', ''))
        
        print(f"✅ Total rows fetched: {len(all_data)} (NULL: {len(null_response.data)}, Empty: {len(empty_response.data)})")
        return all_data
    except Exception as e:
        print(f"❌ Error fetching lenders: {e}")
        return []

def fetch_all_lenders():
    """
    Fetch all lenders from the table.
    """
    try:
        print(f"🔍 Fetching all lenders from table: {SUPABASE_TABLE}")
        response = supabase.table(SUPABASE_TABLE).select("*").execute()
        print(f"✅ Fetched {len(response.data)} rows from Supabase")
        return response.data
    except Exception as e:
        print(f"❌ Error fetching all lenders: {e}")
        return []

def update_row(table_name, update_data, match_column, match_value):
    """
    Update a row in Supabase table using the match column and value.
    """
    try:
        # Normalize and exclude match columns from update
        if match_column in update_data:
            update_data.pop(match_column)

        if not update_data:
            print("⚠️ No fields to update after excluding match columns.")
            return

        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone).isoformat()

        # Update the row using Supabase
        response = supabase.table(table_name).update(update_data).eq(match_column, match_value).execute()
        
        if response.data:
            print(f"✅ Updated row where {match_column} = {match_value}")
        else:
            print(f"⚠️ No rows matched for {match_column} = {match_value}")
            
    except Exception as e:
        print(f"❌ Error updating row {match_column} = {match_value}: {e}")
        raise





################################################### WORKFLOW ###################################################
# # filtered = filter_urls_by_keywords(hrefs, domain, keywords)

# # data_path = r"C:\Users\Asheem Siwach\Downloads\Python_bank_URLs.xlsx"
# # lender_input_data = load_input_data(data_path = data_path)

# # lender_name = lender_input_data.loc[0,"Lender"]
# # homeloan_website = lender_input_data.loc[0,"Homeloan_Website"]
# # domain = extract_base_url(homeloan_website)

# # Get all rows from the table
# lender_data = fetch_all_rows("select * from lenders_data where updated_at is null")


# # Iterate through the data
# for row in lender_data:
#     lender_name = str(row.get("lender"))
#     homeloan_website = str(row.get("homeloan_website"))
#     domain = extract_base_url(homeloan_website)


#     print("Lender Name:-",lender_name)
#     print("Domain:-",domain)
#     print("Homeloan Website:-",homeloan_website)

#     try:
#         # Extract urls from website
#         extracted_urls = extract_urls_from_website(homeloan_website)
#         hrefs = extracted_urls["hrefs"]
#         paragraphs = extracted_urls["paragraphs"]
#         filtered = filter_urls_by_keywords(hrefs, domain, keywords)
#     except Exception as e:
#         print(f"Error extracting urls from {homeloan_website}: {e}")
    

#     if filtered:
#         filtered = normalize_urls(filtered, homeloan_website)


#     if filtered:
#         try:
#             extracted_data = {}
#             for url in filtered[:50]:
#                 print(f"🔍 Processing: {url}")
#                 text = extract_content_from_url(url, domain=domain)
#                 extracted_data[url] = text  # preview first 1000 characters

#         except Exception as e:
#             print(f"Error extracting data from {homeloan_website}: {e}")


#     if extracted_data:
#         # Filtering the data
#         final_data = []
#         for value in extracted_data.values():
#             splitted_text = value.split("\n")
#             filtered_text = [item for item in splitted_text if item.strip()]
#             for text in filtered_text:
#                 if text not in final_data:
#                     final_data.extend(filtered_text)

#         final_data = ", ".join(final_data)
#         print("Total Data:-",len(final_data), "Type of data:-",type(final_data))


#     if final_data:
#         # 1. Model Response based on URLs data
#         final_data = final_data.replace("{", '(').replace("}", ')')
#         prompt = prompt.format(lender_name=lender_name, final_data=final_data)
#         model_response = gpt_model_response(prompt)
#         parsed_response = model_response.choices[0].message.content

#         model_response_data = json.loads(parsed_response)
#         print("✅ Model Responseded well.")

#         # 2. Search Model to fill empty fields
#         missing_fields = 0
#         for key, value in model_response_data.items():
#             if "Not Found" in value:
#                 search_prompt = f"""Please provide the real financial data realted to the housing loans
#                             provided by the lenders.
#                             KEY: Search for {key} detail from the Lender/Bank : {lender_name}"""
#                 search_response = gpt_search_response(search_prompt)
#                 parsed_search_response = search_response.choices[0].message.content
#                 model_response_data[key] = str(parsed_search_response
#                 )
#                 missing_fields += 1

#         model_response_data["updated_at"] = datetime.now(timezone)
#         print("🔍 Missing Fields:-",missing_fields)

#         # Update records in excel
#         update_row(table_name="lenders_data", update_data=model_response_data, match_column="lender", match_value=lender_name)
#         print(f"✅ Data fetched for - {lender_name} and updated in database.")



# Get all rows from the table where data is not updated
lender_data = fetch_lenders_with_null_updated_at()
print("Total rows fetched:-",len(lender_data))

# Iterate through each lender row
for row in lender_data:
    lender_name = str(row.get("lender"))
    homeloan_website = str(row.get("homeloan_website"))
    official_website = str(row.get("official_website"))
    domain = extract_base_url(homeloan_website)

    print(f"\n➡️ Lender: {lender_name}")
    print("🌐 Domain:", domain)
    print("🔗 Website:", homeloan_website)

    try:
        # Extract URLs and paragraph text from homepage

        # Filtering the urls to get the first url
        homeloan_urls = [url.strip() for url in homeloan_website.strip().splitlines() if url.strip()]
        homeloan_website = homeloan_urls[0] if homeloan_urls else None
        filtered = homeloan_urls[1:] if len(homeloan_urls) > 1 else []

        extracted_urls = extract_urls_from_website(homeloan_website)
        hrefs = extracted_urls.get("hrefs", [])
        paragraphs = extracted_urls.get("paragraphs", [])
        other_urls = filter_urls_by_keywords(hrefs, domain, keywords)

        # combine the other urls with the filtered urls
        filtered = filtered + other_urls

        if not filtered:
            print("⚠️ No URLs matched the keywords. Skipping.")
            continue
        filtered = normalize_urls(filtered, homeloan_website)

        # Remove duplicate urls from the filtered urls
        filtered = list(set(filtered))

        # Extract data from filtered URLs
        extracted_data = {}
        for url in filtered[:50]:
            try:
                print(f"🔍 Scraping URL: {url}")
                text = extract_content_from_url(url, domain=domain)
                extracted_data[url] = text
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")

        if not extracted_data:
            print("⚠️ No data extracted from filtered URLs. Skipping.")
            continue

        # Flatten and de-duplicate data
        print("Extracting data from filtered URLs:")
        final_data = []
        for value in extracted_data.values():
            for line in value.split("\n"):
                cleaned = line.strip()
                if cleaned and cleaned not in final_data:
                    final_data.append(cleaned)
        final_data = ", ".join(final_data)

        if not final_data:
            print("⚠️ No usable data extracted after cleaning. Skipping.")
            continue

        # Prepare and call GPT model
        cleaned_data = final_data.replace("{", "(").replace("}", ")")
        prompt_data = prompt.format(lender_name=lender_name, final_data=cleaned_data)
        model_response = gpt_model_response(prompt_data)
        parsed_response = model_response.choices[0].message.content
        
        try:
            model_response_data = json.loads(parsed_response)
        except Exception as e:
            print(f"❌ Failed to parse model response JSON: {e}")
            continue

        print("✅ Primary model responded successfully.")
        
        # Fill missing fields using GPT search
        missing_fields = 0
        for key, value in model_response_data.items():
            if value in ["Not Found","Not Found.","Not found","Not found."]:
                search_prompt = (
                f"Please provide the real financial data related to the housing loans "
                f"provided by the lenders.\nKEY: Search for {key} detail from the Lender/Bank: {lender_name}\n"
                "Your response should include only the values related to the key in numerical data or words less than 10."
                "STRICTLY: Do not provide any source information or urls."
                )
                try:
                    search_response = gpt_search_response(search_prompt)
                    parsed_search = search_response.choices[0].message.content
                    model_response_data[key] = clean_model_response(str(parsed_search))
                    missing_fields += 1
                except Exception as e:
                    print(f"❌ GPT Search failed for key '{key}': {e}")

        model_response_data["updated_at"] = datetime.now(timezone)
        model_response_data['homeloan_website'] = homeloan_website
        model_response_data['official_website'] = official_website

        # Save to database
        update_row(
            table_name="lenders_data",
            update_data=model_response_data,
            match_column="lender",
            match_value=lender_name
        )
        print(f"✅ Data saved for: {lender_name} | 🔍 Missing fields filled: {missing_fields}")
        pass

    except:
        # temporary_filter = ["AU Small Finance Bank Ltd.","Bank of Baroda","Central Bank of India","ICICI Bank Ltd.",
        # "IFL Housing Finance Limited", "Manappuram Home Finance Limited","PNB Housing Finance Limited","Punjab & Sind Bank",
        # "South Indian Bank Ltd.","UCO Bank","Union Bank of India","Yes Bank Ltd."]

        temporary_filter = ["Aadhar Housing Finance Limited","Fincare Small Finance Bank Ltd.","Hero Housing Finance Limited",
        "Indiabulls Housing Finance Limited (now Sammaan Capital)", "Jio Payments Bank Ltd.", "JM Financial Home Loans Limited",
        "Karnataka Bank Ltd.","Khush Housing Finance Limited","Mamta Housing Finance Company Private Limited","Nainital Bank Ltd.",
        "North East Region Housing Finance Company Limited","New Habitat Housing Finance and Development Limited",
        "National Trust Housing Finance Limited", "Ujjivan Small Finance Bank Ltd.","Punjab & Sind Bank","Paytm Payments Bank Ltd."]

        if lender_name in temporary_filter:
            print(f"⚠️ Model processing failed for {lender_name}. Falling back to search prompts.")
        
            model_response_data = {}
            model_response_data["homeloan_website"] = homeloan_website
            model_response_data["official_website"] = official_website
            model_response_data["lender"] = lender_name
            model_response_data["alias"] = ""
            model_response_data["other_urls"] = ""

            for key, value in key_prompt_map.items():
                search_prompt = f"""Please provide the real financial data related to the housing loans.
                Find {value} from the Lender/Bank: {lender_name}
                STRICTLY: Do not provide any source information or urls and keep the response very short and concise."""
                try:
                        search_response = gpt_search_response(search_prompt)
                        parsed_search = search_response.choices[0].message.content
                        model_response_data[key] = clean_model_response(str(parsed_search))
                except Exception as e:
                    print(f"❌ GPT Search failed for key '{key}': {e}")
                print(f"✅ GPT Search successful for key '{key}'")

            model_response_data["updated_at"] = datetime.now(timezone)
            update_row(
                table_name="lenders_data",
                update_data=model_response_data,
                match_column="lender",
                match_value=lender_name
            )
            print(f"✅ Data saved for: {lender_name} using search model.")
        else:
            pass

    finally:
        print(f"✅ Finished processing lender: {lender_name}")

