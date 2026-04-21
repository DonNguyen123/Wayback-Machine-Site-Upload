import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys

SITEMAP_URL = "https://widget-hub.com/sitemap.xml"
WAYBACK_SUBMIT_URL = "https://web.archive.org/save/"
REQUEST_DELAY_SECONDS = 6
MAX_URLS_PER_DAY = 200

def fetch_sitemap_urls(sitemap_url):
    response = requests.get(sitemap_url)
    response.raise_for_status()
    
    root = ET.fromstring(response.content)
    
    namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = []
    
    for loc in root.findall('.//ns:loc', namespaces):
        urls.append(loc.text)
    
    return urls

def archive_url(url):
    submit_url = f"{WAYBACK_SUBMIT_URL}{url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; ArchiveBot/1.0; +https://widget-hub.com)'
    }
    
    try:
        response = requests.get(submit_url, headers=headers, allow_redirects=True, timeout=60)
        
        if response.status_code == 200:
            archive_url_found = None
            if 'Location' in response.headers:
                archive_url_found = response.headers['Location']
            return True, archive_url_found
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    print(f"{datetime.now().isoformat()} - Starting archive process")
    print(f"Sitemap URL: {SITEMAP_URL}")
    print(f"Delay between requests: {REQUEST_DELAY_SECONDS} seconds ({60/REQUEST_DELAY_SECONDS:.0f} per minute)")
    print(f"Daily limit (no account): {MAX_URLS_PER_DAY} URLs")
    print("-" * 50)
    
    urls = fetch_sitemap_urls(SITEMAP_URL)
    print(f"Found {len(urls)} URLs in sitemap")
    
    if len(urls) > MAX_URLS_PER_DAY:
        print(f"WARNING: {len(urls)} URLs exceeds daily limit of {MAX_URLS_PER_DAY}")
        print(f"Only the first {MAX_URLS_PER_DAY} will be processed today")
        urls = urls[:MAX_URLS_PER_DAY]
    
    success_count = 0
    fail_count = 0
    results_log = []
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Archiving: {url}")
        
        success, result = archive_url(url)
        
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