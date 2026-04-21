import requests
import sys

SITEMAP_URL = "https://widget-hub.com/sitemap.xml"

print(f"Fetching: {SITEMAP_URL}")
print("-" * 50)

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(SITEMAP_URL, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
    print(f"Content Length: {len(response.content)} bytes")
    print("-" * 50)
    print("First 500 characters of response:")
    print("-" * 50)
    print(response.text[:500])
    print("-" * 50)
    
    if response.status_code == 200:
        print("Response received successfully")
    else:
        print(f"ERROR: HTTP {response.status_code}")
        
except Exception as e:
    print(f"EXCEPTION: {e}")

sys.exit(0)