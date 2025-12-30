import logging
import time
import json
import os
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup as bs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from models.headline import Headline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
URL = "https://www.nu.nl/meest-gelezen"
DEBUG_DIR = "debug"
# os.makedirs(DEBUG_DIR, exist_ok=True)  # Removed top-level directory creation

# Configure session with retry logic
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
    respect_retry_after_header=True
)
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10
)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Rotating user agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15"
]

def get_random_user_agent() -> str:
    """Return a random user agent from the list."""
    import random
    return random.choice(USER_AGENTS)

def get_headers() -> Dict[str, str]:
    """Return headers with a random user agent."""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
    }

def save_debug_info(filename: str, content: Any, content_type: str = "html") -> None:
    """Save debug information to a file if directory exists."""
    try:
        if not os.path.exists(DEBUG_DIR):
            return
        path = os.path.join(DEBUG_DIR, filename)
        if content_type == "json":
            with open(f"{path}.json", "w", encoding="utf-8") as f:
                if isinstance(content, (dict, list)):
                    json.dump(content, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(content))
        else:
            with open(f"{path}.html", "w", encoding="utf-8") as f:
                f.write(str(content))
        logger.debug(f"Saved debug info to {path}")
    except Exception as e:
        logger.error(f"Failed to save debug info: {e}")

def fetch_with_retry(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Fetch URL with retry logic and exponential backoff."""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            headers = get_headers()
            logger.info(f"Attempt {attempt + 1}: Fetching {url}")
            
            response = session.get(
                url, 
                headers=headers, 
                timeout=15,
                allow_redirects=True,
                verify=True
            )
            
            # Save response for debugging
            save_debug_info(f"raw_response_{attempt}", response.text)
            
            # Check for privacy gate
            if "privacy" in response.url or "privacy-gate" in response.text:
                logger.info("Hit privacy gate, attempting bypass...")
                import re
                from urllib.parse import unquote
                
                # Try to find the callback URL in the script tag
                match = re.search(r"decodeURIComponent\('(.*?)'\)", response.text)
                if match:
                    callback_encoded = match.group(1)
                    callback_url = unquote(callback_encoded)
                    logger.info(f"Following privacy callback: {callback_url}")
                    
                    # Small delay to mimic human interaction if needed, though session usually works
                    time.sleep(1)
                    
                    response = session.get(
                        callback_url,
                        headers=headers,
                        timeout=15,
                        allow_redirects=True
                    )
                    logger.info(f"Privacy bypass response status: {response.status_code}")
                    save_debug_info(f"bypass_response_{attempt}", response.text)
                else:
                    logger.warning("Could not find privacy callback URL")

            response.raise_for_status()
            
            # Check if we got a valid HTML response
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.error(f"Unexpected content type: {content_type}")
                continue
                
            return response
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            wait_time = (2 ** attempt) + (random.random() * 2)
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts: {str(last_exception)}")
    return None

def extract_headlines_from_api(soup: bs) -> List[Dict[str, Any]]:
    """Try to extract headlines from potential JSON-LD or other script tags."""
    headlines = []
    
    # Try to find JSON-LD data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'ItemList' and 'itemListElement' in item:
                        for i, element in enumerate(item['itemListElement'], 1):
                            if 'url' in element and 'name' in element:
                                headlines.append({
                                    'title': element['name'],
                                    'url': element['url'],
                                    'rank': i
                                })
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"Error parsing JSON-LD: {e}")
            continue
    
    return headlines

def scrape_headlines() -> List[Headline]:
    """Scrape most read headlines from nu.nl."""
    logger.info(f"Fetching most read articles from {URL}")
    
    # Save the URL being accessed
    logger.debug(f"Accessing URL: {URL}")
    
    response = fetch_with_retry(URL)
    if not response or not response.text:
        logger.error("Failed to fetch or empty response from the server")
        return []
    
    # Save the full response for debugging
    save_debug_info("full_response", response.text)
    
    try:
        # Try different parsers if the default one fails
        parsers = ['html.parser', 'lxml', 'html5lib']
        soup = None
        
        for parser in parsers:
            try:
                soup = bs(response.text, parser)
                # Test if we can find something with this parser
                if soup.find('body'):
                    logger.debug(f"Successfully parsed with {parser}")
                    break
            except Exception as e:
                logger.debug(f"Parser {parser} failed: {e}")
                continue
        
        if not soup:
            logger.error("Failed to parse HTML with any parser")
            return []
            
        # Save the parsed HTML for debugging
        save_debug_info("parsed_html", soup.prettify())
        
        # Try to extract from potential API data first
        api_headlines = extract_headlines_from_api(soup)
        if api_headlines:
            logger.info(f"Found {len(api_headlines)} headlines from API data")
            return [
                Headline(
                    title=h['title'],
                    summary="",
                    url=h['url'],
                    rank=h['rank']
                ) for h in api_headlines
            ]
        
        # If no API data, try CSS selectors
        selectors = [
            "a.link-block--thumb",
            "a.link-block",
            "ul.contentlist > li > a",
            ".list--numbered > li > a",
            "[data-testid='most-read-articles'] a",
            "div[class*='list'] > a",
            "a[class*='title']",
            "h3 > a",
            "a[href*='/artikel/']",
            "div[class*='item'] > a",
            "article > a"
        ]
        
        nu_headlines = []
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    # Filter only links that look like articles
                    filtered = [
                        el for el in elements 
                        if el.get('href') and 
                           any(p in el['href'] for p in ['/artikel/', '/nieuws/', '.html'])
                    ]
                    if filtered:
                        nu_headlines = filtered
                        logger.info(f"Using selector: {selector}")
                        save_debug_info("selected_elements", [str(el) for el in nu_headlines], "json")
                        break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if not nu_headlines:
            logger.error("No headlines found with any selector")
            # Try to find any links that might be articles
            all_links = soup.find_all('a', href=True)
            article_links = [
                a for a in all_links 
                if any(p in a['href'] for p in ['/artikel/', '/nieuws/', '.html'])
                and (a.get_text(strip=True) or a.get('data-teaser-title'))
            ]
            
            if article_links:
                logger.info(f"Found {len(article_links)} potential article links")
                nu_headlines = article_links
            else:
                logger.error("No article links found in the page")
                # Save the page structure for debugging
                save_debug_info("page_structure", soup.prettify())
                return []
        
        # Process the found headlines
        res = []
        seen_urls = set()
        
        for i, headline in enumerate(nu_headlines[:15], 1):  # Limit to top 15
            try:
                # Get URL
                url = headline.get('href', '').strip()
                if not url:
                    continue
                    
                # Make URL absolute if it's relative
                if not url.startswith(('http://', 'https://')):
                    url = f"https://www.nu.nl{url if not url.startswith('/') else ''}{url if url.startswith('/') else ''}"
                
                # Skip duplicates
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Get title - try different methods
                title = headline.get('data-teaser-title')
                if not title:
                    title_elem = headline.find(['span', 'h1', 'h2', 'h3', 'div', 'p'], class_='item-title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                if not title:
                    title = headline.get_text(strip=True)
                
                if not title:
                    # Try to get title from title attribute or other attributes
                    title = headline.get('title', headline.get('aria-label', '')).strip()
                
                if not title or not url:
                    logger.debug(f"Skipping item with missing title or URL: {headline}")
                    continue
                
                # Clean up title
                title = ' '.join(title.split())
                
                res.append(Headline(
                    title=title,
                    summary="",
                    url=url,
                    rank=len(res) + 1,
                ))
                
                logger.debug(f"Added headline {len(res)}: {title[:50]}...")
                
                # Stop if we have enough results
                if len(res) >= 10:
                    break
                    
            except Exception as e:
                logger.warning(f"Error processing headline: {e}")
                logger.debug(f"Problematic element: {headline}")
                continue
        
        if not res:
            logger.error("No valid headlines could be extracted")
            # Save problematic elements for debugging
            save_debug_info("problematic_elements", [str(h) for h in nu_headlines[:5]], "json")
        else:
            logger.info(f"Successfully scraped {len(res)} headlines")
            
        return res
        
    except Exception as e:
        logger.error(f"Error parsing HTML: {str(e)}", exc_info=True)
        return []
