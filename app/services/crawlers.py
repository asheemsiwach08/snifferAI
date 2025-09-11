import requests
from typing import Optional, List
from firecrawl import FirecrawlApp, ScrapeOptions
from app.config.settings import settings


class FirecrawlCrawler:
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.app = FirecrawlApp(api_key=self.api_key)

        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY is not set")
        if not self.app:
            raise ValueError("Failed to initialize FirecrawlApp")

    def scrape_url(self, url: str, formats= ['markdown', 'html'], json_options=None, only_main_content=True, timeout=30000):
        try:
            response = self.app.scrape_url(
                url, 
                formats=formats, 
                json_options=json_options, 
                only_main_content=only_main_content, 
                timeout=timeout)
            return response
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def url_map (self, url: str):
        try:
            response = self.app.map_url(url)
            return response
        except Exception as e:
            print(f"Error mapping {url}: {e}")
            return None


    def url_crawler(self, url: str, limit=10):
        try:
            response = self.app.crawl_url(url, limit=limit, scrape_options=ScrapeOptions(format=['markdown', 'html']))
            return response
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

    def check_crawl_status(self, crawl_id: str):
        try:
            response = self.app.get_crawl_status(crawl_id)
            return response
        except Exception as e:
            print(f"Error checking crawl status {crawl_id}: {e}")
            return None

    def extract_data(self, urls: list[str] = None, prompt: str = None, schema: dict = None):
        try:
            response = self.app.extract(urls, prompt=prompt, schema=schema)
            return {
                        "success": True,
                        "data": response.data,
                        "status":"completed",
                        "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                        "error": None
                    }
        except Exception as e:
            print(f"Error extracting data: {e}")
            return {"success": False, 
                    "data": None,
                    "status":"Not defined",
                    "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                    "error": str(e)
                    }

    def search_data(self, input_data: str = None, limit: int = 3, timeout: int = 30000):
        try:
            response = self.app.search(
                input_data,
                limit=limit,
                tbs="qdr:d",
                timeout=timeout,
                location="India",
                )

            return {
                        "success": response.success, 
                        "data": response,
                        "status":"Completed",
                        "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                        "error": response.error
                    }
        except Exception as e:
            print(f"Error searching data: {e}")
            return {"success": False, 
                    "data": None,
                    "status":"Not defined",
                    "token_usage":{"prompt_token":0,"completion_token":0, "output_token":0, "total_token":0},
                    "error": str(e)
                    }

    def search_crawl_api(self, query: str, location: str, limit: int = 5, timeout: int = 60000):
        url = "https://api.firecrawl.dev/v1/search"

        payload = {
            "limit": 5,
            "timeout": 60000,
            "ignoreInvalidURLs": True,
            "scrapeOptions": {
                "formats": [],
                "onlyMainContent": True,
                "includeTags": [None]
            },
            "query": query,
            "location": location
                }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def scrape_url_api():
        url = "https://api.firecrawl.dev/v1/scrape"

        payload = {
            "zeroDataRetention": False,
            "onlyMainContent": True,
            "maxAge": 0,
            "waitFor": 0,
            "mobile": False,
            "skipTlsVerification": False,
            "timeout": 30000,
            "parsePDF": True,
            "location": { "country": "US" },
            "removeBase64Images": True,
            "blockAds": True,
            "storeInCache": True,
            "formats": ["markdown"],
            "jsonOptions": {
                "systemPrompt": "helololo",
                "prompt": "what is this"
            }
        }
        headers = {
            "Authorization": "Bearer fc-fe348537c6d245bb92f898304d0ab234",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()

    def crawl_url_api(self, url: str):

        url = "https://api.firecrawl.dev/v1/crawl"

        payload = {
            "maxDepth": 2,
            "ignoreSitemap": False,
            "ignoreQueryParameters": False,
            "limit": 10000,
            "allowBackwardLinks": False,
            "crawlEntireDomain": False,
            "allowExternalLinks": False,
            "allowSubdomains": False,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True
            },
            "zeroDataRetention": False,
            "url": url
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.json()

firecrawler = FirecrawlCrawler()


