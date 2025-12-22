#!/usr/bin/env python3
"""
DuoPlus Cloud Phone API Integration Test
API Key: 043fd16c-b586-4292-a431-6e81f40e4402
Documentation: https://help.duoplus.net/docs/api-reference

Based on documentation structure, trying different API endpoints
"""

import requests
import json

# DuoPlus API Configuration
API_KEY = "043fd16c-b586-4292-a431-6e81f40e4402"

# Possible base URLs based on documentation
POSSIBLE_BASE_URLS = [
    "https://api.duoplus.net/api/v1",
    "https://api.duoplus.net/open/v1",
    "https://my.duoplus.net/api/v1",
    "https://openapi.duoplus.net/api/v1",
    "https://openapi.duoplus.net/v1",
]

def test_api_connection(base_url):
    """Test connection to DuoPlus API with different authentication methods"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {base_url}")
    print('='*60)
    
    # Different auth headers to try
    auth_methods = [
        {"Authorization": f"Bearer {API_KEY}"},
        {"Authorization": API_KEY},
        {"Api-Key": API_KEY},
        {"X-Api-Key": API_KEY},
        {"token": API_KEY},
    ]
    
    # Different endpoints to try
    endpoints = [
        "/phone/list",
        "/phones",
        "/device/list",
        "/devices",
        "/user/info",
        "/account/info",
        "",  # Root endpoint
    ]
    
    for auth in auth_methods:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, headers=auth, timeout=10)
                print(f"\n[{response.status_code}] {url}")
                print(f"Headers: {list(auth.keys())}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"SUCCESS! Response: {json.dumps(data, indent=2)[:500]}")
                        return True, base_url, auth
                    except:
                        print(f"Response: {response.text[:200]}")
                elif response.status_code != 404:
                    try:
                        print(f"Response: {response.json()}")
                    except:
                        print(f"Response: {response.text[:200]}")
                        
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {url}")
            except requests.exceptions.Timeout:
                print(f"Timeout: {url}")
            except Exception as e:
                print(f"Error: {e}")
    
    return False, None, None

def main():
    print("DuoPlus API Connection Test")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    
    for base_url in POSSIBLE_BASE_URLS:
        success, url, auth = test_api_connection(base_url)
        if success:
            print(f"\n✅ Found working endpoint: {url}")
            print(f"Auth method: {auth}")
            break
    else:
        print("\n❌ No working endpoint found")
        
    # Also try with POST requests
    print("\n\n" + "="*60)
    print("Trying POST requests...")
    print("="*60)
    
    for base_url in POSSIBLE_BASE_URLS:
        url = f"{base_url}/phone/list"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        try:
            response = requests.post(url, headers=headers, json={}, timeout=10)
            print(f"\n[POST {response.status_code}] {url}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
