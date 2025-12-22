#!/usr/bin/env python3
"""
GeeLark API Test Script
Testing with provided credentials
"""

import requests
import json

# Credentials
APP_ID = "2FC9X9O4798WG301A0811VYO"
BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"

# Possible base URLs
BASE_URLS = [
    "https://open.geelark.com/openapi/v1",
    "https://open.geelark.com/api/v1", 
    "https://api.geelark.com/v1",
    "https://openapi.geelark.com/v1",
]

# Possible endpoints
ENDPOINTS = [
    "/env/list",
    "/profile/list",
    "/profiles",
    "/device/list",
    "/devices",
    "/phone/list",
    "/group/list",
    "/groups",
]

# Different auth headers to try
def get_auth_headers(auth_type):
    if auth_type == "bearer":
        return {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
    elif auth_type == "app_id_bearer":
        return {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "X-App-Id": APP_ID,
            "Content-Type": "application/json"
        }
    elif auth_type == "basic":
        return {
            "Authorization": f"{APP_ID}:{BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
    elif auth_type == "token_header":
        return {
            "X-Api-Key": BEARER_TOKEN,
            "X-App-Id": APP_ID,
            "Content-Type": "application/json"
        }
    return {}

# Body with credentials
def get_body(body_type):
    if body_type == "with_app_id":
        return {"app_id": APP_ID}
    elif body_type == "with_token":
        return {"token": BEARER_TOKEN, "app_id": APP_ID}
    elif body_type == "empty":
        return {}
    return {}

print("=" * 60)
print("GeeLark API Connection Test")
print("=" * 60)
print(f"APP ID: {APP_ID}")
print(f"Bearer Token: {BEARER_TOKEN[:10]}...")
print("=" * 60)

successful_calls = []

# Test combinations
for base_url in BASE_URLS:
    for endpoint in ENDPOINTS[:3]:  # Test first 3 endpoints
        url = f"{base_url}{endpoint}"
        
        for auth_type in ["bearer", "app_id_bearer", "token_header"]:
            for body_type in ["empty", "with_app_id"]:
                headers = get_auth_headers(auth_type)
                body = get_body(body_type)
                
                try:
                    # Try POST
                    response = requests.post(url, headers=headers, json=body, timeout=10)
                    
                    # Check if we got JSON response (not HTML)
                    content_type = response.headers.get('Content-Type', '')
                    is_json = 'application/json' in content_type
                    
                    if response.status_code == 200 or is_json:
                        print(f"\n✅ POTENTIAL SUCCESS!")
                        print(f"   URL: {url}")
                        print(f"   Method: POST")
                        print(f"   Auth: {auth_type}")
                        print(f"   Body: {body_type}")
                        print(f"   Status: {response.status_code}")
                        print(f"   Content-Type: {content_type}")
                        try:
                            data = response.json()
                            print(f"   Response: {json.dumps(data, indent=2)[:500]}")
                            successful_calls.append({
                                "url": url,
                                "auth": auth_type,
                                "body": body_type,
                                "response": data
                            })
                        except:
                            print(f"   Response: {response.text[:200]}")
                    elif response.status_code not in [404, 405, 301, 302]:
                        print(f"\n⚠️  Status {response.status_code}: {url} ({auth_type})")
                        if is_json:
                            try:
                                print(f"   Response: {response.json()}")
                            except:
                                pass
                                
                except requests.exceptions.Timeout:
                    pass
                except requests.exceptions.ConnectionError:
                    pass
                except Exception as e:
                    pass

# Also try GET method on some endpoints
print("\n" + "=" * 60)
print("Testing GET method...")
print("=" * 60)

for base_url in BASE_URLS[:2]:
    for endpoint in ["/env/list", "/profile/list"]:
        url = f"{base_url}{endpoint}"
        headers = get_auth_headers("bearer")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type or response.status_code == 200:
                print(f"\n✅ GET {url}")
                print(f"   Status: {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
        except:
            pass

print("\n" + "=" * 60)
print(f"Summary: Found {len(successful_calls)} successful API calls")
print("=" * 60)

if successful_calls:
    print("\nWorking configuration:")
    for call in successful_calls:
        print(f"  - {call['url']}")
else:
    print("\nNo working endpoints found yet.")
    print("Please check GeeLark API documentation for exact base URL.")
