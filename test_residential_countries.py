import requests
import time

# Для Residential прокси используем country-specific endpoints
password = "gbLZ8rl9y=VlXx37je"
username = "spvzzn2tmc"

# Residential endpoints для нужных стран
# Согласно документации для Residential:
tests = [
    # US endpoint
    ("us.decodo.com", 10001, "🇺🇸 USA"),
    # UK endpoint  
    ("gb.decodo.com", 30001, "🇬🇧 UK"),  # UK порты 30001-49999
    # Germany endpoint
    ("de.decodo.com", 20001, "🇩🇪 Germany"),  # DE порты 20001-29999
]

print("=" * 60)
print("🌍 Тест Residential Proxies по странам")
print("=" * 60)

working = []

for host, port, country_name in tests:
    proxy_url = f"http://{username}:{password}@{host}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    print(f"\n🎯 {country_name}")
    print(f"   Endpoint: {host}:{port}")
    
    try:
        resp = requests.get(
            "https://ip.decodo.com/json",
            proxies=proxies,
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            country = data.get('country', {})
            city = data.get('city', {})
            
            if isinstance(country, dict):
                country_code = country.get('code', 'N/A')
                country_nm = country.get('name', 'N/A')
            else:
                country_code = 'N/A'
                country_nm = country
                
            if isinstance(city, dict):
                city_name = city.get('name', 'N/A')
                tz = city.get('time_zone', 'N/A')
            else:
                city_name = city
                tz = 'N/A'
            
            print(f"   ✅ {country_nm} ({country_code})")
            print(f"   📍 {city_name}")
            print(f"   🕐 {tz}")
            working.append((host, port, country_code))
        else:
            print(f"   ❌ HTTP {resp.status_code}")
    except requests.exceptions.ProxyError as e:
        print(f"   ❌ Proxy Error: {str(e)[:60]}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:60]}")
    
    time.sleep(2)

print("\n" + "=" * 60)
print(f"📊 Работающих: {len(working)}/3")
print("=" * 60)

if len(working) >= 2:
    print("\n✅ Прокси готовы для Instagram!")
