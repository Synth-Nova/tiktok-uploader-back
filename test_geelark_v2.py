#!/usr/bin/env python3
"""
GeeLark API Test - Version 2
Try different URL patterns and auth methods
"""

import requests
import json

APP_ID = "2FC9X9O4798WG301A0811VYO"
BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"

print("Testing GeeLark API with various patterns...")
print("=" * 70)

# Different URL patterns to try
test_cases = [
    # Pattern 1: openapi subdomain
    ("POST", "https://openapi.geelark.com/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    ("POST", "https://openapi.geelark.com/v1/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    
    # Pattern 2: open.geelark with different paths
    ("POST", "https://open.geelark.com/openapi/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    ("POST", "https://open.geelark.com/v1/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    
    # Pattern 3: With app_id in body
    ("POST", "https://open.geelark.com/openapi/v1/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {"app_id": APP_ID}),
    ("POST", "https://open.geelark.com/openapi/v1/env/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {"app_id": APP_ID}),
    
    # Pattern 4: Different header combinations
    ("POST", "https://open.geelark.com/openapi/v1/profile/list", {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "X-App-Id": APP_ID,
        "X-Request-Id": "test123"
    }, {}),
    
    # Pattern 5: api.geelark.com
    ("POST", "https://api.geelark.com/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    ("POST", "https://api.geelark.com/openapi/v1/profile/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    
    # Pattern 6: No Bearer prefix
    ("POST", "https://open.geelark.com/openapi/v1/profile/list", {"Authorization": BEARER_TOKEN}, {}),
    ("POST", "https://open.geelark.com/openapi/v1/profile/list", {"Token": BEARER_TOKEN}, {}),
    
    # Pattern 7: With both credentials
    ("POST", "https://open.geelark.com/openapi/v1/profile/list", {
        "Content-Type": "application/json"
    }, {"app_id": APP_ID, "token": BEARER_TOKEN}),
    
    # Pattern 8: Group list
    ("POST", "https://open.geelark.com/openapi/v1/group/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    
    # Pattern 9: CloudPhone endpoints  
    ("POST", "https://open.geelark.com/openapi/v1/cloudphone/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    ("POST", "https://open.geelark.com/openapi/v1/phone/list", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    
    # Pattern 10: Different endpoint naming
    ("POST", "https://open.geelark.com/openapi/v1/profiles", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
    ("POST", "https://open.geelark.com/openapi/v1/profile/query", {"Authorization": f"Bearer {BEARER_TOKEN}"}, {}),
]

for method, url, headers, body in test_cases:
    headers["Content-Type"] = "application/json"
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=10)
        else:
            resp = requests.get(url, headers=headers, timeout=10)
        
        content_type = resp.headers.get('Content-Type', '')
        is_html = 'text/html' in content_type
        
        # Skip HTML responses
        if is_html and resp.status_code == 200:
            continue
            
        status_icon = "✅" if resp.status_code == 200 else "❌" if resp.status_code >= 400 else "⚠️"
        
        print(f"\n{status_icon} {method} {url}")
        print(f"   Status: {resp.status_code}")
        print(f"   Content-Type: {content_type}")
        
        if not is_html:
            try:
                data = resp.json()
                print(f"   Response: {json.dumps(data, ensure_ascii=False)[:300]}")
            except:
                text = resp.text[:200]
                if text and not text.startswith('<!DOCTYPE'):
                    print(f"   Response: {text}")
                    
    except requests.exceptions.ConnectionError as e:
        print(f"\n🔴 Connection Error: {url}")
        print(f"   {str(e)[:100]}")
    except Exception as e:
        print(f"\n🔴 Error: {url} - {str(e)[:50]}")

print("\n" + "=" * 70)
print("Test completed. If no JSON responses, API documentation needed.")
