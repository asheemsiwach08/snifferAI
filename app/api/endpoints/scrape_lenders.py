import logging
from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from app.services.database_service import database_service
from app.models.schemas import LendersGeminiSearchResponse, SnifferAIRequest, SnifferAIResponse
from app.services.gemini_service import gemini_service
from app.services.llm_services import openai_analyzer

logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/scrape_lenders")
def scrape_lenders(request: SnifferAIRequest):
    try:
        logger.info(f"Scraping lenders for request: {request}")

        generate_response = gemini_service.generate_search_response(
            prompt="""What is the 
                1. interest rate, 
                2. Loan-to-value, 
                3. minimum credit score, 
                4. loan amount range, 
                5. loan tenure range, 
                6. approval time, 
                7. processing fee, 
                8. special Offers
                for home loan in India for {}.""".format(request.entity),
            model="gemini-2.0-flash"
        )
        search_response = generate_response["response"]

        llm_response, token_usage = openai_analyzer.gpt_model_structured_response(
            system_message="You are a helpful assistant which can extract the information from the data provided by the user. Parse that data into valuable structured response and provide the response in JSON format.", 
            prompt=str(search_response), 
            model="gpt-4o-mini", 
            response_format=LendersGeminiSearchResponse
        )

        structured_response = llm_response.choices[0].message.parsed
        structured_response_dict = structured_response.model_dump()

        # Reformat the response based on the keys in the response format
        structured_response_dict["lender"] = request.entity
        structured_response_dict["ROI (Rate of Interest)"] = structured_response_dict.pop("interest_rate_range")
        structured_response_dict["LTV (Loan-to-Value)"] = structured_response_dict.pop("loan_to_value")
        structured_response_dict["Minimum Credit Score"] = structured_response_dict.pop("minimum_credit_score")
        structured_response_dict["Approval Time"] = structured_response_dict.pop("approval_time")
        structured_response_dict["Loan Amount Range"] = structured_response_dict.pop("loan_amount_range")
        structured_response_dict["Loan Tenure Range"] = structured_response_dict.pop("loan_tenure_range")
        structured_response_dict["Processing Fee"] = structured_response_dict.pop("processing_fee")
        structured_response_dict["Special Offers"] = structured_response_dict.pop("special_offers")

        # save the structured response to the database
        database_response = database_service.save_unique_data(data=structured_response_dict, table_name="lenders_google_search", primary_key="lender", update_if_exists=True)
        

        return {"message": f"Data scraped & {database_response['status']} - {database_response['message']} successfully"}
    except Exception as e:
        logger.error(f"Error scraping lenders: {e}")
        raise HTTPException(status_code=500, detail=str(e))