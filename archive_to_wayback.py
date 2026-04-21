import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

SITEMAP_URL = "https://widget-hub.com/sitemap.xml"
WAYBACK_SUBMIT_URL = "https://web.archive.org/save/"
REQUEST_DELAY_SECONDS = 10
MAX_URLS_PER_DAY = 200
MAX_RETRIES = 3
RETRY_DELAY = 30

def log_print(message):
    print(message)
    sys.stdout.flush()

def fetch_sitemap_urls(sitemap_url):
    log_print(f"Fetching sitemap from {sitemap_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    response = requests.get(sitemap_url, headers=headers, timeout=30)
    response.raise_for_status()
    log_print(f"Sitemap fetched: {len(response.content)} bytes")
    
    content = response.content
    
    try:
        root = ET.fromstring(content)
        log_print("XML parsed successfully")
    except ET.ParseError as e:
        log_print(f"XML Parse Error: {e}")
        log_print("Attempting to remove comments and retry...")
        import re
        content_str = response.text
        content_str_no_comments = re.sub(r'<!--.*?-->', '', content_str, flags=re.DOTALL)
        root = ET.fromstring(content_str_no_comments)
        log_print("XML parsed after comment removal")
    
    urls = []
    for url_element in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        urls.append(url_element.text)
    
    log_print(f"Found {len(urls)} URLs in sitemap")
    return urls

def archive_url(url, attempt=1):
    submit_url = f"{WAYBACK_SUBMIT_URL}{url}"
    log_print(f"  Attempt {attempt}/{MAX_RETRIES} for {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'close'
    }
    
    try:
        log_print(f"  Sending request to web.archive.org...")
        response = requests.get(submit_url, headers=headers, allow_redirects=True, timeout=90)
        log_print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            archive_url_found = response.headers.get('Location', 'Archived')
            log_print(f"  SUCCESS: {archive_url_found}")
            return True, archive_url_found
        elif response.status_code == 429 and attempt < MAX_RETRIES:
            log_print(f"  RATE LIMITED (429). Waiting {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return archive_url(url, attempt+1)
        else:
            log_print(f"  FAILED: HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        log_print(f"  TIMEOUT error")
        if attempt < MAX_RETRIES:
            log_print(f"  Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return archive_url(url, attempt+1)
        else:
            return False, "Timeout after retries"
            
    except requests.exceptions.ConnectionError as e:
        log_print(f"  CONNECTION ERROR: {str(e)[:80]}")
        if attempt < MAX_RETRIES:
            log_print(f"  Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return archive_url(url, attempt+1)
        else:
            return False, f"Connection error: {str(e)[:60]}"
            
    except Exception as e:
        log_print(f"  UNKNOWN ERROR: {str(e)[:80]}")
        return False, str(e)[:80]

def main():
    log_print("=" * 60)
    log_print(f"STARTING ARCHIVE PROCESS at {datetime.now().isoformat()}")
    log_print("=" * 60)
    log_print(f"Sitemap URL: {SITEMAP_URL}")
    log_print(f"Delay between requests: {REQUEST_DELAY_SECONDS} seconds")
    log_print(f"Max retries per URL: {MAX_RETRIES}")
    log_print("-" * 60)
    
    urls = fetch_sitemap_urls(SITEMAP_URL)
    
    if len(urls) > MAX_URLS_PER_DAY:
        log_print(f"WARNING: {len(urls)} URLs exceeds daily limit of {MAX_URLS_PER_DAY}")
        log_print(f"Only the first {MAX_URLS_PER_DAY} will be processed today")
        urls = urls[:MAX_URLS_PER_DAY]
    
    log_print("-" * 60)
    log_print(f"Processing {len(urls)} URLs...")
    log_print("-" * 60)
    
    success_count = 0
    fail_count = 0
    results_log = []
    
    for i, url in enumerate(urls, 1):
        log_print(f"\n[{i}/{len(urls)}] URL: {url}")
        
        success, result = archive_url(url)
        
        if success:
            success_count += 1
            results_log.append(f"SUCCESS: {url} -> {result}")
        else:
            fail_count += 1
            results_log.append(f"FAILED: {url} - {result}")
        
        log_print(f"  Progress: {success_count} success, {fail_count} failed")
        
        if i < len(urls):
            log_print(f"  Waiting {REQUEST_DELAY_SECONDS} seconds before next URL...")
            time.sleep(REQUEST_DELAY_SECONDS)
    
    log_print("-" * 60)
    log_print(f"COMPLETED at {datetime.now().isoformat()}")
    log_print(f"Final stats - Success: {success_count}, Failed: {fail_count}, Total: {len(urls)}")
    log_print("=" * 60)
    
    with open("archive_results.txt", "w") as f:
        f.write(f"Archive run completed at {datetime.now().isoformat()}\n")
        f.write(f"Success: {success_count}, Failed: {fail_count}\n")
        f.write("-" * 60 + "\n")
        for line in results_log:
            f.write(line + "\n")
    
    if fail_count > 0:
        log_print(f"WARNING: {fail_count} failures occurred")
        sys.exit(1)
    else:
        log_print("All URLs archived successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_print("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)