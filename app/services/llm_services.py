import logging
from google import genai
from google.genai import types
from openai import OpenAI
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIAnalyzer:
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.client = OpenAI(api_key=self.api_key)

        if not self.client:
            raise ValueError("Failed to initialize OpenAI client")

    def analyze_context(self, model: str = None, messages: list = None, response_format=None):
        if not model:
            model = self.model

        try:
            response = self.client.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_format,
                # temperature=temperature
            )
            return {
                    "success": True,
                    "data":response.choices[0].message.parsed.model_dump(),
                    "status":"Not defined",
                    "token_usage":{"prompt_token":response.usage.prompt_tokens,"completion_token":response.usage.completion_tokens, "output_token":0, "total_token":response.usage.total_tokens},
                    "error": None
                }
        except Exception as e:
            return {
                    "success": False,
                    "data":None,
                    "status":"Error",
                    "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                    "error": str(e)
                }


        
    # Function to send a prompt to GPT model for extracting data
    def get_structured_response(self, system_message, prompt, model: str = None, response_format=None):
        try:
            response = self.client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # creativity
                response_format=response_format
            )
            
            return {
                    "success": True,
                    "data":response.choices[0].message.parsed.model_dump(),
                    "status":"Not defined",
                    "token_usage":{
                        "prompt_token":response.usage.prompt_tokens,
                        "completion_token":response.usage.completion_tokens, 
                        "output_token":0, 
                        "total_token":response.usage.total_tokens
                        },
                    "error": None
                }
        except Exception as e:
            return {
                    "success": False,
                    "data":None,
                    "status":"Error",
                    "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                    "error": str(e)
                }

    def structured_output(self, prompt, model: str = None, response_format=None):
        try:
            response = self.client.responses.parse(
                model=model,
                temperature=0.7,
                input=[
                        {"role": "system", "content": "Extract entities from the input text"},
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                text_format=response_format
            )
            if response.output_parsed:
                return {
                    "success": True,
                    "data":response.output_parsed.model_dump(),
                    "status":response.status,
                    "token_usage":{
                        "prompt_token":response.usage.input_tokens, 
                        "completion_token":0,
                        "output_token":response.usage.output_tokens, 
                        "total_token":response.usage.total_tokens
                        },
                    "error": response.error
                }
            
        except Exception as e:
            return {
                    "success": False,
                    "data":None,
                    "status":"Error",
                    "token_usage":{"input_token":0, "output_token":0, "total_token":0},
                    "error": str(e)
                }


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
        if not self.client:
            logger.error("❌ Failed to initialize Gemini client")
            raise ValueError("Failed to initialize Gemini client")

        # Define the grounding tool
        self.grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Configure generation settings
        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool]
        )

        logger.info("✅ Gemini service initialized successfully")

    def search_google(self,prompt, model:str = "gemini-2.0-flash"):
        """Generate a search response using Gemini"""
        response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=self.config,
            )
        
        if response.candidates:
            try:
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        return {
                                "success": True,
                                "data":part.text,
                                "status":"completed",
                                "token_usage":{
                                    "prompt_token":response.usage_metadata.prompt_token_count,
                                    "completion_token":response.usage_metadata.candidates_token_count, 
                                    "output_token":0, 
                                    "total_token":response.usage_metadata.total_token_count
                                    },
                                "error": None
                            }
                        
                else:
                    return {
                        "success": False,
                        "data": None,
                        "status":"completed",
                        "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                        "error": None
                    }
            except Exception as e:
                logger.error(f"Error searching Google: {e}")
                return {
                        "success": False,
                        "data": None,
                        "status":"completed",
                        "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                        "error": str(e)
                    }
                


openai_analyzer = OpenAIAnalyzer()
gemini_service = GeminiService()
