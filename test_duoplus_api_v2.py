#!/usr/bin/env python3
"""
DuoPlus Cloud Phone API Integration - Extended Test
Trying to find correct API endpoints and authentication
"""

import requests
import json

# DuoPlus API Configuration
API_KEY = "043fd16c-b586-4292-a431-6e81f40e4402"
BASE_URL = "https://api.duoplus.net/api/v1"

def make_request(method, endpoint, data=None, params=None):
    """Make API request with detailed logging"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=15)
        else:
            response = requests.post(url, headers=headers, json=data or {}, timeout=15)
        
        print(f"\n[{method} {response.status_code}] {endpoint}")
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except:
            print(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("DuoPlus API - Extended Endpoint Discovery")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print("="*60)
    
    # Test various endpoints based on DuoPlus documentation structure
    endpoints_to_test = [
        # Phone/Device management
        ("GET", "/phone/list"),
        ("POST", "/phone/list"),
        ("GET", "/phone/info"),
        ("POST", "/phone/info"),
        ("GET", "/cloud-phone/list"),
        ("POST", "/cloud-phone/list"),
        ("GET", "/device/list"),
        
        # Power operations
        ("POST", "/phone/powerOn"),
        ("POST", "/phone/power-on"),
        ("POST", "/phone/start"),
        ("POST", "/phone/powerOff"),
        ("POST", "/phone/power-off"),
        ("POST", "/phone/stop"),
        
        # File operations
        ("POST", "/phone/uploadFile"),
        ("POST", "/phone/upload-file"),
        ("POST", "/file/push"),
        ("POST", "/file-push"),
        
        # User/Account info
        ("GET", "/user/info"),
        ("POST", "/user/info"),
        ("GET", "/account"),
        ("GET", "/me"),
        ("GET", "/profile"),
        
        # Groups
        ("GET", "/group/list"),
        ("POST", "/group/list"),
        
        # RPA
        ("GET", "/rpa/task/list"),
        ("POST", "/rpa/task/list"),
        ("GET", "/task/list"),
        ("POST", "/task/list"),
    ]
    
    results = {}
    for method, endpoint in endpoints_to_test:
        result = make_request(method, endpoint)
        if result and result.get("code") != 160002:
            results[endpoint] = result
            
    print("\n" + "="*60)
    print("Summary of responses (excluding permission errors):")
    print("="*60)
    for endpoint, result in results.items():
        print(f"{endpoint}: {result}")

if __name__ == "__main__":
    main()
