import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

class Settings:
    "Application Settings"

    # API configuration
    API_TITLE = "Sniffer AI"
    API_DESCRIPTION = "Sniffer AI is a tool that allows you to scrape and analyze websites."
    API_VERSION = "1.0.0"

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", "6000")
    RELOAD = os.getenv("RELOAD", "true")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Firecrawl API Key
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

    # OpenAI API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5o-nano")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Gemini API Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")



# Global Settings Instance
settings = Settings()