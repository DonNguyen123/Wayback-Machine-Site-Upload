import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SITEMAP_URL = "https://widget-hub.com/sitemap.xml"
WAYBACK_SUBMIT_URL = "https://web.archive.org/save/"
REQUEST_DELAY_SECONDS = 10
MAX_URLS_PER_DAY = 200
MAX_RETRIES = 3
RETRY_DELAY = 30

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_sitemap_urls(sitemap_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    session = create_session_with_retries()
    response = session.get(sitemap_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    content = response.content
    
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        import re
        content_str = response.text
        content_str_no_comments = re.sub(r'<!--.*?-->', '', content_str, flags=re.DOTALL)
        root = ET.fromstring(content_str_no_comments)
    
    urls = []
    
    for url_element in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        urls.append(url_element.text)
    
    return urls

def archive_url(url, session, attempt=1):
    submit_url = f"{WAYBACK_SUBMIT_URL}{url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'close'
    }
    
    try:
        response = session.get(submit_url, headers=headers, allow_redirects=True, timeout=90)
        
        if response.status_code == 200:
            archive_url_found = None
            if 'Location' in response.headers:
                archive_url_found = response.headers['Location']
            return True, archive_url_found
        elif response.status_code == 429 and attempt < MAX_RETRIES:
            print(f"  Rate limited (429). Waiting {RETRY_DELAY} seconds before retry {attempt+1}...")
            time.sleep(RETRY_DELAY)
            return archive_url(url, session, attempt+1)
        else:
            return False, f"HTTP {response.status_code}"
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        if attempt < MAX_RETRIES:
            print(f"  Connection error: {str(e)[:50]}. Waiting {RETRY_DELAY} seconds before retry {attempt+1}...")
            time.sleep(RETRY_DELAY)
            return archive_url(url, session, attempt+1)
        else:
            return False, str(e)[:100]

def main():
    print(f"{datetime.now().isoformat()} - Starting archive process")
    print(f"Sitemap URL: {SITEMAP_URL}")
    print(f"Delay between requests: {REQUEST_DELAY_SECONDS} seconds ({60/REQUEST_DELAY_SECONDS:.0f} per minute)")
    print(f"Daily limit (no account): {MAX_URLS_PER_DAY} URLs")
    print(f"Max retries per URL: {MAX_RETRIES}")
    print("-" * 50)
    
    urls = fetch_sitemap_urls(SITEMAP_URL)
    print(f"Found {len(urls)} URLs in sitemap")
    
    if len(urls) > MAX_URLS_PER_DAY:
        print(f"WARNING: {len(urls)} URLs exceeds daily limit of {MAX_URLS_PER_DAY}")
        print(f"Only the first {MAX_URLS_PER_DAY} will be processed today")
        urls = urls[:MAX_URLS_PER_DAY]
    
    session = create_session_with_retries()
    
    success_count = 0
    fail_count = 0
    results_log = []
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Archiving: {url}")
        
        success, result = archive_url(url, session)
        
        if success:
            print(f"  SUCCESS: {result if result else 'Archived'}")
            success_count += 1
            results_log.append(f"SUCCESS: {url} -> {result}")
        else:
            print(f"  FAILED: {result}")
            fail_count += 1
            results_log.append(f"FAILED: {url} - {result}")
        
        if i < len(urls):
            print(f"  Waiting {REQUEST_DELAY_SECONDS} seconds...")
            time.sleep(REQUEST_DELAY_SECONDS)
    
    print("-" * 50)
    print(f"Completed: {datetime.now().isoformat()}")
    print(f"Success: {success_count}, Failed: {fail_count}, Total: {len(urls)}")
    
    with open("archive_results.txt", "w") as f:
        f.write(f"Archive run completed at {datetime.now().isoformat()}\n")
        f.write(f"Success: {success_count}, Failed: {fail_count}\n")
        f.write("-" * 50 + "\n")
        for line in results_log:
            f.write(line + "\n")
    
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()