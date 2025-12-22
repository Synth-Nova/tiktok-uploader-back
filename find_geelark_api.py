#!/usr/bin/env python3
"""
Deep search for GeeLark API endpoints
"""
import requests
import re

session = requests.Session()

# Fetch the JS
js_url = "https://open.geelark.com/assets/index-D8rfSIMj.js"
resp = session.get(js_url, timeout=60)
js = resp.text

print("Searching for API patterns in 1.7MB JS bundle...")
print("="*60)

# Search for specific GeeLark API patterns
patterns_to_find = [
    (r'geelark[^"\']*\.com[^"\']*', "GeeLark domains"),
    (r'https://[^"\']+/v\d+/', "Versioned API URLs"),
    (r'/profile/(?:list|create|delete|update|start|stop)', "Profile endpoints"),
    (r'/env/(?:list|create)', "Env endpoints"),
    (r'/group/(?:list|create)', "Group endpoints"),
    (r'/cloudphone/', "CloudPhone endpoints"),
    (r'/phone/', "Phone endpoints"),
    (r'"url"\s*:\s*"([^"]+)"', "URL configs"),
    (r'request\s*\(\s*{[^}]*url\s*:\s*["\']([^"\']+)["\']', "Request URLs"),
    (r'axios\.[a-z]+\s*\(\s*["\']([^"\']+)["\']', "Axios calls"),
    (r'fetch\s*\(\s*["\']([^"\']+)["\']', "Fetch calls"),
    (r'"baseUrl"\s*:\s*"([^"]+)"', "baseUrl config"),
    (r'"apiUrl"\s*:\s*"([^"]+)"', "apiUrl config"),
    (r'"serverUrl"\s*:\s*"([^"]+)"', "serverUrl config"),
]

for pattern, desc in patterns_to_find:
    matches = re.findall(pattern, js, re.IGNORECASE)
    if matches:
        unique = list(set(matches))[:15]
        print(f"\n✅ {desc}:")
        for m in unique:
            if isinstance(m, tuple):
                print(f"    {m}")
            else:
                print(f"    {m}")

# Search around "Bearer" keyword
print("\n" + "="*60)
print("Searching context around 'Bearer' keyword...")
bearer_pos = js.find('Bearer')
if bearer_pos > -1:
    context = js[max(0, bearer_pos-200):bearer_pos+200]
    print(f"Context: ...{context}...")

# Search around "Authorization"
print("\n" + "="*60)
print("Searching context around 'Authorization' keyword...")
for match in re.finditer(r'Authorization', js):
    pos = match.start()
    context = js[max(0, pos-100):pos+150]
    # Clean up for readability
    context = re.sub(r'\s+', ' ', context)
    print(f"\nFound: ...{context[:200]}...")
    break

# Look for environment variables or config
print("\n" + "="*60)
print("Searching for config/env patterns...")
config_patterns = re.findall(r'(?:VITE_|VUE_APP_|REACT_APP_|process\.env\.)[A-Z_]+', js)
if config_patterns:
    print(f"Found env vars: {set(config_patterns)}")

# Search for open.geelark specific paths
print("\n" + "="*60)
print("Searching for open.geelark paths...")
open_paths = re.findall(r'open\.geelark\.com[^"\']*', js)
if open_paths:
    for p in set(open_paths)[:10]:
        print(f"  {p}")

