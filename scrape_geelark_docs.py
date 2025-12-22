#!/usr/bin/env python3
"""
Scrape GeeLark API documentation using requests with session
"""
import requests
import json
import re

session = requests.Session()

# First get the main page to get any cookies/tokens
print("Fetching GeeLark API docs page...")
resp = session.get("https://open.geelark.com/api", timeout=30)
print(f"Status: {resp.status_code}")
print(f"Cookies: {dict(session.cookies)}")

# Check for any API calls in the page
html = resp.text
print(f"\nPage length: {len(html)} chars")

# Look for API endpoints in JavaScript
api_patterns = [
    r'https?://[^"\']+api[^"\']*',
    r'/api/[^"\']+',
    r'/openapi/[^"\']+',
    r'"(POST|GET)"\s*,\s*"([^"]+)"',
    r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)',
    r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)',
]

print("\nSearching for API patterns in page...")
for pattern in api_patterns:
    matches = re.findall(pattern, html)
    if matches:
        print(f"\nPattern: {pattern}")
        for m in matches[:10]:
            print(f"  - {m}")

# Try to find the actual API base URL from assets
assets_match = re.findall(r'src="(/assets/[^"]+\.js)"', html)
print(f"\nFound {len(assets_match)} JS assets")

if assets_match:
    for asset in assets_match[:3]:
        asset_url = f"https://open.geelark.com{asset}"
        print(f"\nFetching: {asset_url}")
        try:
            js_resp = session.get(asset_url, timeout=30)
            js_content = js_resp.text
            
            # Search for API patterns in JS
            api_urls = re.findall(r'["\']?(https?://[^"\']*geelark[^"\']*)["\']?', js_content)
            if api_urls:
                print("  Found URLs:")
                for url in set(api_urls)[:20]:
                    print(f"    - {url}")
            
            # Search for endpoint definitions
            endpoints = re.findall(r'["\']?(/(?:api|openapi)/v\d+/[^"\']+)["\']?', js_content)
            if endpoints:
                print("  Found endpoints:")
                for ep in set(endpoints)[:20]:
                    print(f"    - {ep}")
                    
            # Search for baseURL
            base_urls = re.findall(r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']', js_content)
            if base_urls:
                print("  Found baseURLs:")
                for bu in set(base_urls):
                    print(f"    - {bu}")
                    
        except Exception as e:
            print(f"  Error: {e}")

