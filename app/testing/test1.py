import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.crawlers import firecrawler

def test_firecrawler():
    """Test the firecrawler functionality"""
    
    print("🧪 Testing Firecrawl scraping...")
    
    try:
        url = "https://www.hdfcbank.com/personal/loans/home-loans/home-loan-eligibility-calculator"
        print(f"Scraping URL: {url}")
        
        response = firecrawler.scrape_url(url)
        
        if response:
            print("✅ Scraping successful!")
            print(f"Response type: {type(response)}")
            
            # Print response structure
            if hasattr(response, '__dict__'):
                print("Response attributes:")
                for key, value in response.__dict__.items():
                    print(f"  {key}: {type(value)}")
            
            # If response has content, show a preview
            if hasattr(response, 'content'):
                content = str(response.content)[:500]
                print(f"Content preview: {content}...")
            elif hasattr(response, 'markdown'):
                content = str(response.markdown)[:500]
                print(f"Markdown preview: {content}...")
            else:
                print(f"Response: {str(response)[:500]}...")
                
        else:
            print("❌ Scraping failed - No response received")
            
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")

if __name__ == "__main__":
    test_firecrawler()