import requests
import time

proxies_data = [
    ("gate.decodo.com", 10001, "spvzzn2tmc", "gbLZ8rl9y=VlXx37je"),
    ("gate.decodo.com", 10002, "spvzzn2tmc", "gbLZ8rl9y=VlXx37je"),
    ("gate.decodo.com", 10003, "spvzzn2tmc", "gbLZ8rl9y=VlXx37je"),
]

print("=" * 60)
print("🔍 Проверка Decodo Residential Proxies")
print("=" * 60)

working = 0
for host, port, user, password in proxies_data:
    proxy_url = f"http://{user}:{password}@{host}:{port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    print(f"\n📌 Тест: {host}:{port}")
    try:
        # Проверяем IP
        resp = requests.get(
            "https://ip.decodo.com/json",
            proxies=proxies,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Работает!")
            print(f"   IP: {data.get('ip', 'N/A')}")
            print(f"   Страна: {data.get('country', 'N/A')} ({data.get('country_code', 'N/A')})")
            print(f"   Город: {data.get('city', 'N/A')}")
            print(f"   ISP: {data.get('asn', {}).get('org', 'N/A')}")
            working += 1
        else:
            print(f"   ❌ Ошибка: HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    time.sleep(1)

print("\n" + "=" * 60)
print(f"📊 Результат: {working}/3 прокси работают")
print("=" * 60)

if working > 0:
    print("\n✅ Прокси готовы к использованию!")
    print("\n📋 Следующий шаг: настройка по странам")
    print("   USA: user-spvzzn2tmc-country-us")
    print("   UK:  user-spvzzn2tmc-country-gb")
    print("   DE:  user-spvzzn2tmc-country-de")
