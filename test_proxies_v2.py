import requests
import time

# Попробуем разные форматы username для country targeting
password = "gbLZ8rl9y=VlXx37je"
host = "gate.decodo.com"

# Разные варианты форматов
test_formats = [
    # Формат 1: spvzzn2tmc-country-us
    ("spvzzn2tmc-country-us", 10001, "Format 1: base-country-XX"),
    
    # Формат 2: user-spvzzn2tmc-country-us (уже пробовали)
    # ("user-spvzzn2tmc-country-us", 10001, "Format 2: user-base-country-XX"),
    
    # Формат 3: spvzzn2tmc с портом для US (7777 для US в Decodo)
    ("spvzzn2tmc", 7777, "Format 3: US port 7777"),
    
    # Формат 4: Residential specific ports
    ("spvzzn2tmc", 10001, "Format 4: Residential default"),
]

print("=" * 60)
print("🔍 Тест разных форматов Decodo")
print("=" * 60)

for username, port, desc in test_formats:
    proxy_url = f"http://{username}:{password}@{host}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    print(f"\n📌 {desc}")
    print(f"   {username}@{host}:{port}")
    
    try:
        resp = requests.get("https://ip.decodo.com/json", proxies=proxies, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            country = data.get('country', {})
            if isinstance(country, dict):
                print(f"   ✅ {country.get('name', 'N/A')} ({country.get('code', 'N/A')})")
            else:
                print(f"   ✅ {country}")
        else:
            print(f"   ❌ HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ {str(e)[:50]}")
    
    time.sleep(1)

# Попробуем через endpoint с country code
print("\n" + "=" * 60)
print("🌍 Тест через country-specific endpoints")
print("=" * 60)

country_endpoints = [
    ("us.decodo.com", 10001, "US endpoint"),
    ("gb.decodo.com", 10001, "UK endpoint"),
    ("de.decodo.com", 10001, "DE endpoint"),
]

for endpoint, port, desc in country_endpoints:
    proxy_url = f"http://spvzzn2tmc:{password}@{endpoint}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    print(f"\n📌 {desc}: {endpoint}:{port}")
    
    try:
        resp = requests.get("https://ip.decodo.com/json", proxies=proxies, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            country = data.get('country', {})
            if isinstance(country, dict):
                print(f"   ✅ {country.get('name', 'N/A')} ({country.get('code', 'N/A')})")
            else:
                print(f"   ✅ {country}")
        else:
            print(f"   ❌ HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ {str(e)[:60]}")
    
    time.sleep(1)
