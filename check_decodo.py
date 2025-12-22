import requests
import json

# API ключ пользователя
API_KEY = "04d02ef9c45ecc44d8b85b18797ca2005af5b35a6f829368f6d6cf515a77235b9b2feb61b531b3d0d3f0728efef9f8755194ea6c5b8f8abb97673fee22518299d2a22ead3e56e3aa49d3bdee4d03e98d9e8c0354c16490"

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("🔍 Проверка Decodo API")
print("=" * 60)

# Проверяем разные endpoints
endpoints = [
    ("https://api.decodo.com/v1/users/me", "User Info"),
    ("https://api.decodo.com/v2/users/me", "User Info v2"),
    ("https://api.decodo.com/v1/subscriptions", "Subscriptions"),
    ("https://api.decodo.com/v2/subscriptions", "Subscriptions v2"),
]

for url, name in endpoints:
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"\n📌 {name} ({url})")
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"   Response: {resp.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

# Попробуем другой формат авторизации
print("\n" + "=" * 60)
print("🔍 Пробуем Basic Auth")
print("=" * 60)

import base64
auth_string = base64.b64encode(f"{API_KEY}:".encode()).decode()
headers_basic = {
    "Authorization": f"Basic {auth_string}",
}

try:
    resp = requests.get("https://api.decodo.com/v2/subscriptions", headers=headers_basic, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

