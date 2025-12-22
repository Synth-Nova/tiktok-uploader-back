#!/usr/bin/env python3
"""
Scrape GeeLark API documentation - find endpoints in JS
"""
import requests
import re

session = requests.Session()

# Fetch main JS bundle
print("Fetching main JS bundle...")
js_url = "https://open.geelark.com/assets/index-D8rfSIMj.js"
resp = session.get(js_url, timeout=60)
js_content = resp.text
print(f"JS file size: {len(js_content)} chars")

# Find all API-related patterns
print("\n" + "="*60)
print("Searching for API endpoints...")
print("="*60)

# Pattern 1: URL paths
url_patterns = re.findall(r'["\']/((?:api|openapi)/[^"\']+)["\']', js_content)
if url_patterns:
    print("\n📍 Found URL paths:")
    for p in sorted(set(url_patterns))[:30]:
        print(f"  /{p}")

# Pattern 2: Full URLs with geelark
full_urls = re.findall(r'https?://[a-zA-Z0-9.-]*geelark\.com[^"\'>\s]*', js_content)
if full_urls:
    print("\n🌐 Found full URLs:")
    for u in sorted(set(full_urls))[:20]:
        print(f"  {u}")

# Pattern 3: baseURL definitions
base_patterns = re.findall(r'baseURL\s*[:=]\s*["\']([^"\']+)["\']', js_content)
if base_patterns:
    print("\n🔧 Found baseURL:")
    for b in set(base_patterns):
        print(f"  {b}")

# Pattern 4: Look for profile/env/group related
profile_patterns = re.findall(r'["\'][^"\']*(?:profile|env|group|phone|device|cloudphone)[^"\']*["\']', js_content, re.IGNORECASE)
if profile_patterns:
    print("\n📱 Profile/Device related strings:")
    seen = set()
    for p in profile_patterns[:50]:
        clean = p.strip("'\"")
        if clean not in seen and len(clean) < 100 and '/' in clean:
            seen.add(clean)
            print(f"  {clean}")

# Pattern 5: HTTP method + path combinations
method_patterns = re.findall(r'(post|get|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', js_content, re.IGNORECASE)
if method_patterns:
    print("\n🔄 HTTP methods found:")
    for method, path in method_patterns[:30]:
        print(f"  {method.upper()} {path}")

# Pattern 6: Look for "Authorization" or "Bearer" patterns
auth_patterns = re.findall(r'["\']?(Authorization|Bearer|X-Api-Key|token)["\']?\s*[:=]\s*[`"\']([^`"\']+)[`"\']', js_content, re.IGNORECASE)
if auth_patterns:
    print("\n🔑 Auth patterns:")
    for key, val in auth_patterns[:10]:
        print(f"  {key}: {val[:50]}...")

