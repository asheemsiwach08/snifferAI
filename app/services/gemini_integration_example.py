"""
Example integration of Gemini service with Sniffer AI functionality
"""

from app.services.gemini_service import gemini_service
from app.models.schemas import LendersExtractSchema
import json

def integrate_gemini_with_sniffer():
    """
    Example of how to integrate Gemini service with your sniffer functionality
    """
    
    # Example 1: Use Gemini for data extraction instead of OpenAI
    def extract_lender_data_with_gemini(scraped_content: str, lender_name: str):
        """Extract lender data using Gemini"""
        
        # Create extraction prompt
        prompt = f"""
        Extract detailed information about {lender_name} from the following content.
        Focus on loan rates, fees, eligibility criteria, and other financial details.
        
        Content:
        {scraped_content}
        """
        
        # Get schema from your existing model
        schema = LendersExtractSchema.model_json_schema()
        
        # Use Gemini for extraction
        result = gemini_service.extract_structured_data(
            prompt=prompt,
            schema=schema,
            system_message="You are a financial data extraction expert. Extract accurate loan information.",
            model="gemini-1.5-pro"
        )
        
        return result
    
    # Example 2: Use Gemini for content analysis
    def analyze_scraped_content(content: str):
        """Analyze scraped content using Gemini"""
        
        result = gemini_service.analyze_content(
            content=content,
            analysis_type="financial_data",
            model="gemini-1.5-flash"
        )
        
        return result
    
    # Example 3: Use Gemini for data refinement
    def refine_extracted_data(raw_data: dict):
        """Refine extracted data using Gemini"""
        
        refinement_rules = {
            "interest_rate": "Convert to decimal format (e.g., 8.75)",
            "loan_amount": "Standardize to INR format",
            "processing_fee": "Convert to decimal percentage",
            "tenure": "Convert to years format"
        }
        
        result = gemini_service.refine_data(
            original_data=raw_data,
            refinement_rules=refinement_rules,
            model="gemini-1.5-pro"
        )
        
        return result
    
    # Example 4: Use Gemini for search and extraction
    def search_for_specific_info(content: str, search_terms: list):
        """Search for specific information in content"""
        
        search_query = " ".join(search_terms)
        extraction_fields = ["interest_rate", "processing_fee", "eligibility_criteria"]
        
        result = gemini_service.search_and_extract(
            search_query=search_query,
            content=content,
            extraction_fields=extraction_fields,
            model="gemini-1.5-pro"
        )
        
        return result
    
    return {
        "extract_lender_data": extract_lender_data_with_gemini,
        "analyze_content": analyze_scraped_content,
        "refine_data": refine_extracted_data,
        "search_extract": search_for_specific_info
    }

# Example usage in your sniffer endpoint
def example_sniffer_integration():
    """
    Example of how to modify your sniffer endpoint to use Gemini
    """
    
    # Sample scraped content
    sample_content = """
    HDFC Bank offers home loans with interest rates starting from 8.75% p.a.
    The minimum loan amount is ₹5 lakhs and maximum is ₹10 crores.
    Processing fee is 0.5% of the loan amount.
    Loan tenure ranges from 5 to 30 years.
    Eligibility includes salaried and self-employed individuals.
    """
    
    # Get integration functions
    gemini_functions = integrate_gemini_with_sniffer()
    
    print("🚀 Gemini Integration Examples")
    print("=" * 50)
    
    # Example 1: Extract structured data
    print("\n1. Structured Data Extraction:")
    extraction_result = gemini_functions["extract_lender_data"](sample_content, "HDFC Bank")
    if extraction_result["success"]:
        print("✅ Extraction successful!")
        print(f"Data: {json.dumps(extraction_result['data'], indent=2)}")
    else:
        print(f"❌ Extraction failed: {extraction_result['error']}")
    
    # Example 2: Content analysis
    print("\n2. Content Analysis:")
    analysis_result = gemini_functions["analyze_content"](sample_content)
    if analysis_result["success"]:
        print("✅ Analysis successful!")
        print(f"Analysis: {analysis_result['response']}")
    else:
        print(f"❌ Analysis failed: {analysis_result['error']}")
    
    # Example 3: Data refinement
    print("\n3. Data Refinement:")
    raw_data = {
        "lender": "HDFC Bank",
        "interest_rate": "8.75% p.a.",
        "loan_amount": "₹5,00,000 to ₹10,00,000",
        "processing_fee": "0.5% of loan amount"
    }
    refinement_result = gemini_functions["refine_data"](raw_data)
    if refinement_result["success"]:
        print("✅ Refinement successful!")
        print(f"Refined: {refinement_result['data']}")
    else:
        print(f"❌ Refinement failed: {refinement_result['error']}")
    
    # Example 4: Search and extract
    print("\n4. Search and Extract:")
    search_result = gemini_functions["search_extract"](sample_content, ["interest rate", "processing fee"])
    if search_result["success"]:
        print("✅ Search successful!")
        print(f"Found: {search_result['response']}")
    else:
        print(f"❌ Search failed: {search_result['error']}")

if __name__ == "__main__":
    example_sniffer_integration()
