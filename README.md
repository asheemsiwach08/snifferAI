# 🕵️ SniffrAI

**SniffrAI** is an intelligent web scraping and data extraction tool that uses AI to automatically classify, extract, and store structured data from websites. It combines web scraping, LLM-powered data processing, and automatic database management.

## 🚀 Features

- **🤖 AI-Powered Classification**: Automatically classifies data based on content and URLs
- **🔍 Multi-Tool Extraction**: Supports Google Search, FireCrawl, and custom scrapers
- **📊 Dynamic Schema Generation**: Creates Pydantic models on-the-fly based on data structure
- **🗄️ Automatic Database Management**: Creates tables and handles data storage automatically
- **🆔 Smart Primary Key Handling**: Generates UUIDs for missing primary keys
- **🔄 Data Refinement**: AI-powered data cleaning and structuring
- **📈 Batch Processing**: Handles multiple records efficiently
- **🛡️ Error Handling**: Comprehensive error handling and logging

## 🏗️ Architecture

```
SniffrAI/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── sniffer.py          # Main API endpoint
│   │   │   └── scrape_lenders.py   # Specialized scrapers
│   │   └── routes.py               # API routing
│   ├── config/
│   │   ├── logger.py               # Logging configuration
│   │   └── settings.py             # Application settings
│   ├── models/
│   │   └── schemas.py              # Pydantic models
│   ├── services/
│   │   ├── crawlers.py             # Web crawling services
│   │   ├── database_service.py     # Database operations
│   │   ├── gemini_service.py       # Google Gemini integration
│   │   ├── llm_services.py         # LLM processing
│   │   └── sniffer_services.py     # Core sniffer logic
│   └── utils/
│       ├── prompts.py              # AI prompts
│       └── validators.py           # Data validation
├── config.yaml                     # Configuration file
└── requirements.txt                # Python dependencies
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database (via Supabase)
- API keys for:
  - OpenAI
  - Google Gemini
  - FireCrawl
  - Supabase

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SniffrAI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   FIRECRAWL_API_KEY=your_firecrawl_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
   ```

5. **Configure Settings**
   Update `config.yaml` with your use cases and configurations.

6. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📖 Usage

### Basic API Request

```python
import requests

# Basic scraping request
data = {
    "urls": ["https://example-bank.com/home-loans"],
    "snifferTool": True,
    "enableRefinement": True
}

response = requests.post("http://localhost:8000/api/sniffer_ai", json=data)
print(response.json())
```

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `urls` | List[str] | URLs to scrape (required) |
| `snifferTool` | bool | Enable FireCrawl scraping |
| `googleSearch` | bool | Enable Google search |
| `enableRefinement` | bool | Enable AI data refinement |
| `prompt` | str | Additional context for scraping |

### Response Format

```json
{
    "success": true,
    "message": "Data extraction completed successfully"
}
```

## 🔧 Configuration

### Use Cases Configuration (`config.yaml`)

```yaml
use_cases:
  lenders:
    keywords: ["interest", "roi", "loan", "bank"]
    table_name: "lenders_data"
    primary_key: "lender"
    output_format: "LendersGeminiSearchResponse"
    scraper_system_message: "lenders_system_message"
    scraper_prompt: "lenders_scraper_prompt"
    refinement_prompt: "lenders_refinement_prompt"
    
  doctors:
    keywords: ["doctor", "clinic", "medical"]
    table_name: "doctors_data"
    primary_key: "name"
    output_format: "SnifferExtractSchema"
```

### Adding New Use Cases

1. **Add to config.yaml**
2. **Create corresponding Pydantic schema in `models/schemas.py`**
3. **Add schema mapping in `api/endpoints/sniffer.py`**

## 🗄️ Database Schema

SniffrAI automatically creates tables with the following structure:

```sql
CREATE TABLE your_table (
    id TEXT PRIMARY KEY,                    -- Auto-generated UUID
    your_unique_field TEXT UNIQUE,         -- Business unique field
    data_field_1 TEXT,
    data_field_2 TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Key Features:
- **Fixed Primary Key**: Always `id` with UUID
- **Unique Constraints**: Business fields marked as unique
- **Automatic Timestamps**: `created_at` and `updated_at`
- **UUID Generation**: Automatic for missing primary keys

## 🤖 AI Components

### 1. Classification Agent
Automatically classifies incoming requests based on URLs and content.

### 2. Config Generation Agent
Generates dynamic configurations for new use cases.

### 3. Data Extraction
Uses FireCrawl and custom scrapers for data extraction.

### 4. Refinement Agent
Cleans and structures extracted data using LLMs.

## 📊 Supported Data Sources

- **Financial Institutions**: Banks, lenders, loan providers
- **Healthcare**: Doctors, clinics, medical services  
- **Professional Services**: Consultants, advisors
- **Custom**: Configurable for any domain

## 🔍 Example Use Cases

### 1. Lender Data Extraction
```python
{
    "urls": ["https://bank.com/home-loans"],
    "snifferTool": True,
    "enableRefinement": True
}
```

**Extracts**: Interest rates, loan terms, eligibility criteria, etc.

### 2. Doctor Directory Scraping
```python
{
    "urls": ["https://medical-directory.com"],
    "snifferTool": True
}
```

**Extracts**: Doctor names, specializations, contact info, etc.

### 3. Google Search Integration
```python
{
    "urls": ["example.com"],
    "googleSearch": True,
    "prompt": "Find loan information"
}
```

**Searches**: Google for relevant information and extracts data.

## 🛡️ Error Handling

- **Validation**: Input validation for all requests
- **Retry Logic**: Automatic retries for failed operations
- **Logging**: Comprehensive logging for debugging
- **Graceful Degradation**: Fallback mechanisms for failures

## 📈 Performance

- **Batch Processing**: Handles multiple records efficiently
- **Async Operations**: Non-blocking I/O operations
- **Caching**: Intelligent caching of responses
- **Rate Limiting**: Respects API rate limits

## 🔒 Security

- **API Key Management**: Secure handling of API keys
- **Input Sanitization**: Prevents injection attacks
- **CORS Configuration**: Proper CORS setup
- **Environment Isolation**: Separate environments for dev/prod

## 📝 API Documentation

### Endpoints

#### `POST /api/sniffer_ai`
Main endpoint for data extraction and processing.

**Request Body:**
```json
{
    "urls": ["string"],
    "snifferTool": boolean,
    "googleSearch": boolean,
    "enableRefinement": boolean,
    "prompt": "string"
}
```

**Response:**
```json
{
    "success": boolean,
    "message": "string"
}
```

## 🧪 Testing

Run tests using:
```bash
python -m pytest tests/
```

Test files are located in `app/testing/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for debugging

## 🔄 Changelog

### v1.0.0
- Initial release
- Basic web scraping functionality
- AI-powered classification
- Automatic database management
- UUID primary key generation

---

**Built with ❤️ using FastAPI, Pydantic, and AI**
