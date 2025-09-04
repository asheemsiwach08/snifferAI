"""
Simple Webpage Content Extractor
"""

import requests
from bs4 import BeautifulSoup
import time
import io
import pandas as pd

from PyPDF2 import PdfReader
import pytz
import time
import urllib3
from urllib.parse import urlparse, urljoin
# Disable SSL warnings when verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set timezone (e.g., Asia/Kolkata, UTC, US/Eastern)
timezone = pytz.timezone('Asia/Kolkata')

# SSL Configuration - you can modify these based on your needs
SSL_VERIFY = False  # Set to True if you want to enable SSL verification
SSL_CERT_PATH = None  # Path to certificate file if needed
TIMEOUT_SECONDS = 15  # Request timeout

# Helper function to get SSL configuration
def get_ssl_config():
    """Return SSL configuration for requests"""
    config = {
        'verify': SSL_VERIFY,
        'timeout': TIMEOUT_SECONDS
    }
    
    if SSL_CERT_PATH:
        config['cert'] = SSL_CERT_PATH
    
    return config

def extract_response_content(response):
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    # Extract different types of content
    title = soup.find('title')
    title_text = title.get_text().strip() if title else "No title found"

    # Get all text content
    text_content = soup.get_text()

    # Clean up the text
    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = ' '.join(chunk for chunk in chunks if chunk)

    # Extract all links
    links = []
    for link in soup.find_all('a', href=True):
        links.append({
            'text': link.get_text().strip(),
            'url': link['href']
        })

    # Extract headings
    headings = []
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        headings.append({
            'level': heading.name,
            'text': heading.get_text().strip()
        })

    # Extract paragraphs
    paragraphs = []
    for para in soup.find_all('p'):
        para_text = para.get_text().strip()
        if para_text:  # Only add non-empty paragraphs
            paragraphs.append(para_text)

    return {
        'status': 'success',
        'url': url,
        'title': title_text,
        'content': clean_text,
        'content_length': len(clean_text),
        'links': links[:10],  # Limit to first 10 links
        'headings': headings[:10],  # Limit to first 10 headings
        'paragraphs': paragraphs[:10],  # Limit to first 10 paragraphs
        'status_code': response.status_code,
        'extraction_time': time.time()
    }


# Helper function to get browser headers
def get_browser_headers():
    """Return headers that make the request look like it's coming from a real browser"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

# Helper function to add delays between requests
def add_request_delay(delay_seconds=1):
    """Add a delay to avoid rate limiting"""
    time.sleep(delay_seconds)

# Helper function to make requests with retry logic
def make_request_with_retry(url, max_retries=3, delay_between_retries=2):
    """Make HTTP request with retry logic for handling temporary failures"""
    headers = get_browser_headers()
    ssl_config = get_ssl_config()
    
    print(f"🌐 Making HTTP request to: {url}")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, **ssl_config)
            response.raise_for_status()
            print(f"✅ HTTP {response.status_code} - Content-Type: {response.headers.get('content-type', 'Unknown')}")
            return response
        except requests.exceptions.SSLError as ssl_error:
            print(f"🔒 SSL Error on attempt {attempt + 1} for {url}: {ssl_error}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying with different SSL configuration...")
                # Try with different SSL settings on retry
                try:
                    response = requests.get(url, headers=headers, verify=False, timeout=TIMEOUT_SECONDS)
                    response.raise_for_status()
                    print(f"✅ HTTP {response.status_code} - Content-Type: {response.headers.get('content-type', 'Unknown')} (SSL verification disabled)")
                    return response
                except Exception as retry_error:
                    print(f"❌ Retry attempt {attempt + 1} also failed: {retry_error}")
                    if attempt < max_retries - 1:
                        time.sleep(delay_between_retries)
            else:
                print(f"❌ All {max_retries} attempts failed for {url} due to SSL errors")
                raise ssl_error
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}. Retrying in {delay_between_retries} seconds...")
                time.sleep(delay_between_retries)
            else:
                print(f"❌ All {max_retries} attempts failed for {url}: {e}")
                raise e



def extract_webpage_content(url, timeout=30):
    """
    Extract text content from any webpage
    
    Args:
        url (str): URL of the webpage
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: Extracted content with metadata
    """
    try:
        headers = {}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Extract different types of content
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"

        # Get all text content
        text_content = soup.get_text()

        # Clean up the text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)

        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                'text': link.get_text().strip(),
                'url': link['href']
            })

        # Extract headings
        headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': heading.name,
                'text': heading.get_text().strip()
            })

        # Extract paragraphs
        paragraphs = []
        for para in soup.find_all('p'):
            para_text = para.get_text().strip()
            if para_text:  # Only add non-empty paragraphs
                paragraphs.append(para_text)

        return {
            'status': 'success',
            'url': url,
            'title': title_text,
            'content': clean_text,
            'content_length': len(clean_text),
            'links': links[:10],  # Limit to first 10 links
            'headings': headings[:10],  # Limit to first 10 headings
            'paragraphs': paragraphs[:10],  # Limit to first 10 paragraphs
            'status_code': response.status_code,
            'extraction_time': time.time()
        }

    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'url': url,
            'error': f"Request error: {str(e)}",
            'extraction_time': time.time()
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': f"Extraction error: {str(e)}",
            'extraction_time': time.time()
        }

def extract_multiple_pages(urls, delay=1):
    """
    Extract content from multiple webpages
    
    Args:
        urls (list): List of URLs
        delay (int): Delay between requests in seconds
        
    Returns:
        list: List of extraction results
    """
    results = []
    
    for i, url in enumerate(urls):
        print(f"Extracting {i+1}/{len(urls)}: {url}")
        
        result = extract_webpage_content(url)
        results.append(result)
        
        # Add delay between requests
        if i < len(urls) - 1:  # Don't delay after the last request
            time.sleep(delay)
    
    return results


# Extract the base url from the full url
def extract_base_url(full_url):
    parsed = urlparse(full_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    return base_url

# Extract all hrefs and paragraphs from the website
def extract_urls_from_website(homeloan_website):
    try:
        # Use retry logic to handle temporary failures
        response = make_request_with_retry(homeloan_website)
        
        # Add delay to avoid rate limiting
        add_request_delay(1)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Step 1: Extract all <a href="..."> links
        hrefs = [a['href'] for a in soup.find_all('a', href=True)]

        # Step 2: Extract all <p> paragraph text
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

        return {"hrefs":hrefs,"paragraphs":paragraphs}
    except Exception as e:
        print(f"❌ Error extracting urls from {homeloan_website}: {e}")
        return {"hrefs":[],"paragraphs":[]}

# Filter urls by keywords
def filter_urls_by_keywords(urls, keywords):
    try:
        matched_urls = []
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
    except Exception as e:
        print(f"❌ Error filtering urls by keywords: {e}")
        return []
    

# Normalize urls
def normalize_urls(raw_urls, base_domain):
    try:
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
    except Exception as e:
        print(f"❌ Error normalizing urls: {e}")
        return []

# Supported extensions and their handlers for extracting content from urls
def extract_content_from_url(url,domain):
    if not url.startswith("http"):
        url = domain +"/"+ url
    try:
        # Use retry logic to handle temporary failures
        response = make_request_with_retry(url)
        
        # Add delay to avoid rate limiting
        add_request_delay(0.5)
        
        content = response.content

        # Determine file extension
        path = urlparse(url).path
        extension = path.split('.')[-1].lower()

        if extension == 'pdf':
            with io.BytesIO(content) as f:
                reader = PdfReader(f)
                return '\n'.join([page.extract_text() or '' for page in reader.pages])

        elif extension in ['xls', 'xlsx']:
            with io.BytesIO(content) as f:
                df = pd.read_excel(f, dtype=str)
                return df.to_string(index=False)

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



################################################### Method Flow ###################################################


