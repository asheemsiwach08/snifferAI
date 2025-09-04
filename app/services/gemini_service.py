import logging
from google import genai
from google.genai import types
from app.config.settings import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for handling Google Gemini AI interactions"""
    
    def __init__(self):
        """Initialize Gemini service with API key"""
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        

        # Initialize models
        self.client = genai.Client(api_key=self.api_key)
        
        # Define the grounding tool
        self.grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Configure generation settings
        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool]
        )
        
        logger.info("✅ Gemini service initialized successfully")

    def generate_search_response(self,model, prompt):

        response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
        
        for part in response.candidates[0].content.parts:
            print(response)
            print("---------------------------------------------------------------------------------------------")
            print(part)
            if part.text is not None:
                return {
                    "success": True,
                    "response": part.text,
                    "model": model
                }
            else:
                return {
                    "success": False,
                    "error": "No text in the response",
                    "model": model
                }

        # return response
    
    # def generate_text(self, 
    #                  prompt: str, 
    #                  system_message: str = None,
    #                  model: str = "gemini-1.5-flash",
    #                  temperature: float = 0.7,
    #                  max_tokens: int = 1000) -> Dict[str, Any]:
    #     """
    #     Generate text response using Gemini
        
    #     Args:
    #         prompt (str): User prompt
    #         system_message (str): System message/context
    #         model (str): Model to use ('gemini-1.5-pro' or 'gemini-1.5-flash')
    #         temperature (float): Creativity level (0.0 to 1.0)
    #         max_tokens (int): Maximum tokens to generate
            
    #     Returns:
    #         Dict containing response and metadata
    #     """
    #     try:
    #         # Select model
    #         if model == "gemini-1.5-pro":
    #             genai_model = self.gemini_pro
    #         else:
    #             genai_model = self.gemini_flash
            
    #         # Prepare messages
    #         messages = []
    #         if system_message:
    #             messages.append({"role": "user", "parts": [system_message]})
    #         messages.append({"role": "user", "parts": [prompt]})
            
    #         # Generate response
    #         response = genai_model.generate_content(
    #             messages,
    #             config=self.config,
    #             generation_config=genai.types.GenerationConfig(
    #                 tools=[self.grounding_tool],
    #                 temperature=temperature,
    #                 max_output_tokens=max_tokens,
    #             )
    #         )
            
    #         return {
    #             "success": True,
    #             "response": response.text,
    #             "model": model,
    #             "usage": {
    #                 "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
    #                 "response_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
    #                 "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
    #             }
    #         }
            
    #     except Exception as e:
    #         logger.error(f"❌ Error generating text with Gemini: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "model": model
    #         }
    
    # def extract_structured_data(self, 
    #                           prompt: str,
    #                           schema: Dict[str, Any],
    #                           system_message: str = None,
    #                           model: str = "gemini-1.5-pro") -> Dict[str, Any]:
    #     """
    #     Extract structured data using Gemini with JSON schema
        
    #     Args:
    #         prompt (str): Extraction prompt
    #         schema (Dict): JSON schema for expected output
    #         system_message (str): System message
    #         model (str): Model to use
            
    #     Returns:
    #         Dict containing extracted data and metadata
    #     """
    #     try:
    #         # Create structured prompt
    #         structured_prompt = f"""
    #         {system_message or "You are a data extraction assistant. Extract information according to the schema provided."}
            
    #         SCHEMA:
    #         {schema}
            
    #         PROMPT:
    #         {prompt}
            
    #         Please respond with a valid JSON object matching the schema above.
    #         """
            
    #         # Generate response
    #         result = self.generate_text(
    #             prompt=structured_prompt,
    #             model=model,
    #             temperature=0.1,  # Lower temperature for more consistent extraction
    #             max_tokens=2000
    #         )
            
    #         if result["success"]:
    #             # Try to parse JSON from response
    #             import json
    #             try:
    #                 # Extract JSON from response (handle markdown code blocks)
    #                 response_text = result["response"]
    #                 if "```json" in response_text:
    #                     json_start = response_text.find("```json") + 7
    #                     json_end = response_text.find("```", json_start)
    #                     json_str = response_text[json_start:json_end].strip()
    #                 elif "```" in response_text:
    #                     json_start = response_text.find("```") + 3
    #                     json_end = response_text.find("```", json_start)
    #                     json_str = response_text[json_start:json_end].strip()
    #                 else:
    #                     json_str = response_text.strip()
                    
    #                 extracted_data = json.loads(json_str)
                    
    #                 return {
    #                     "success": True,
    #                     "data": extracted_data,
    #                     "model": model,
    #                     "usage": result.get("usage", {})
    #                 }
                    
    #             except json.JSONDecodeError as e:
    #                 logger.error(f"❌ Failed to parse JSON from response: {e}")
    #                 return {
    #                     "success": False,
    #                     "error": f"Invalid JSON response: {e}",
    #                     "raw_response": result["response"],
    #                     "model": model
    #                 }
    #         else:
    #             return result
                
    #     except Exception as e:
    #         logger.error(f"❌ Error in structured data extraction: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "model": model
    #         }
    
    # def analyze_content(self, 
    #                    content: str,
    #                    analysis_type: str = "general",
    #                    model: str = "gemini-1.5-flash") -> Dict[str, Any]:
    #     """
    #     Analyze content using Gemini
        
    #     Args:
    #         content (str): Content to analyze
    #         analysis_type (str): Type of analysis ('general', 'sentiment', 'summary', 'extract_keywords')
    #         model (str): Model to use
            
    #     Returns:
    #         Dict containing analysis results
    #     """
    #     try:
    #         # Define analysis prompts
    #         analysis_prompts = {
    #             "general": "Please analyze the following content and provide insights:",
    #             "sentiment": "Analyze the sentiment of the following content (positive, negative, neutral):",
    #             "summary": "Provide a concise summary of the following content:",
    #             "extract_keywords": "Extract key terms and important keywords from the following content:",
    #             "financial_data": "Extract financial information, rates, fees, and terms from the following content:"
    #         }
            
    #         prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['general'])}\n\n{content}"
            
    #         result = self.generate_text(
    #             prompt=prompt,
    #             model=model,
    #             temperature=0.3,
    #             max_tokens=1000
    #         )
            
    #         return result
            
    #     except Exception as e:
    #         logger.error(f"❌ Error in content analysis: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "model": model
    #         }
    
    # def search_and_extract(self, 
    #                       search_query: str,
    #                       content: str,
    #                       extraction_fields: List[str],
    #                       model: str = "gemini-1.5-pro") -> Dict[str, Any]:
    #     """
    #     Search content and extract specific fields
        
    #     Args:
    #         search_query (str): What to search for
    #         content (str): Content to search in
    #         extraction_fields (List[str]): Fields to extract
    #         model (str): Model to use
            
    #     Returns:
    #         Dict containing extracted fields
    #     """
    #     try:
    #         prompt = f"""
    #         Search the following content for information related to: {search_query}
            
    #         Extract the following fields:
    #         {', '.join(extraction_fields)}
            
    #         Content:
    #         {content}
            
    #         Please provide the extracted information in a structured format.
    #         """
            
    #         result = self.generate_text(
    #             prompt=prompt,
    #             model=model,
    #             temperature=0.2,
    #             max_tokens=1500
    #         )
            
    #         return result
            
    #     except Exception as e:
    #         logger.error(f"❌ Error in search and extract: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "model": model
    #         }
    
# Create a singleton instance
gemini_service = GeminiService()
