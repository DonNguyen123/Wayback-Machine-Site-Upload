import requests
import sys
from datetime import datetime

SITEMAP_URL = "https://widget-hub.com/sitemap.xml"
WAYBACK_SITEMAP_API = "https://web.archive.org/sitemap/submit"

def log_print(message):
    print(message)
    sys.stdout.flush()

def submit_sitemap():
    log_print("=" * 60)
    log_print(f"Submitting sitemap to Wayback Machine at {datetime.now().isoformat()}")
    log_print(f"Sitemap URL: {SITEMAP_URL}")
    log_print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        log_print("Sending submission request...")
        response = requests.post(
            WAYBACK_SITEMAP_API,
            data={"sitemap": SITEMAP_URL},
            headers=headers,
            timeout=30
        )
        
        log_print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            log_print("SUCCESS: Sitemap submitted to Wayback Machine")
            log_print("Wayback Machine will now crawl and archive all URLs at their own pace")
            return True
        else:
            log_print(f"FAILED: HTTP {response.status_code}")
            log_print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_print(f"ERROR: {str(e)}")
        return False

def main():
    success = submit_sitemap()
    
    # Write results file for GitHub Actions artifact
    with open("archive_results.txt", "w") as f:
        f.write(f"Archive submission completed at {datetime.now().isoformat()}\n")
        if success:
            f.write("Status: SUCCESS - Sitemap submitted\n")
            f.write(f"Sitemap URL: {SITEMAP_URL}\n")
            f.write("Wayback Machine will archive all URLs from the sitemap.\n")
        else:
            f.write("Status: FAILED - Could not submit sitemap\n")
    
    log_print("-" * 60)
    log_print(f"COMPLETED at {datetime.now().isoformat()}")
    log_print("=" * 60)
    
    sys.exit(0 if success else 1)

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