import requests
import time

# Тестируем прокси с таргетингом по странам
# Формат: user-USERNAME-country-XX

base_user = "spvzzn2tmc"
password = "gbLZ8rl9y=VlXx37je"
host = "gate.decodo.com"
port = 10001

countries = [
    ("us", "USA"),
    ("gb", "UK"),
    ("de", "Germany"),
]

print("=" * 60)
print("🌍 Проверка прокси по странам (USA, UK, Germany)")
print("=" * 60)

results = []

for country_code, country_name in countries:
    # Формируем username с country targeting
    username = f"user-{base_user}-country-{country_code}"
    
    proxy_url = f"http://{username}:{password}@{host}:{port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    print(f"\n🎯 Тест: {country_name} ({country_code})")
    print(f"   Username: {username}")
    
    try:
        resp = requests.get(
            "https://ip.decodo.com/json",
            proxies=proxies,
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            actual_country = data.get('country', {})
            if isinstance(actual_country, dict):
                actual_code = actual_country.get('code', 'N/A')
                actual_name = actual_country.get('name', 'N/A')
            else:
                actual_code = data.get('country_code', 'N/A')
                actual_name = actual_country
            
            city_data = data.get('city', {})
            if isinstance(city_data, dict):
                city = city_data.get('name', 'N/A')
                timezone = city_data.get('time_zone', 'N/A')
            else:
                city = city_data
                timezone = 'N/A'
            
            match = "✅" if actual_code.lower() == country_code else "⚠️"
            print(f"   {match} Страна: {actual_name} ({actual_code})")
            print(f"   Город: {city}")
            print(f"   Timezone: {timezone}")
            
            results.append({
                "target": country_code,
                "actual": actual_code,
                "match": actual_code.lower() == country_code,
                "city": city
            })
        else:
            print(f"   ❌ HTTP {resp.status_code}")
            results.append({"target": country_code, "actual": None, "match": False})
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        results.append({"target": country_code, "actual": None, "match": False})
    
    time.sleep(2)

print("\n" + "=" * 60)
print("📊 ИТОГ:")
print("=" * 60)

matches = sum(1 for r in results if r.get('match'))
print(f"\nСовпадений: {matches}/{len(results)}")

if matches == len(results):
    print("\n✅ Все прокси работают с правильным геотаргетингом!")
    print("   Готовы к настройке Instagram!")
else:
    print("\n⚠️ Некоторые страны не совпали")
    print("   Возможно нужно настроить sticky session")
