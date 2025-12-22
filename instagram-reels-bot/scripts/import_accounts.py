"""
Import accounts from config file to database
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import init_database, add_account, get_all_accounts
from src.utils.fingerprint_generator import generate_fingerprint

# Load accounts config
config_path = Path(__file__).parent.parent / "config" / "accounts.json"

with open(config_path, 'r') as f:
    config = json.load(f)

print("=" * 60)
print("📥 Importing Instagram Accounts to Database")
print("=" * 60)

# Initialize database
init_database()

# Import each account
imported = 0
for acc in config['accounts']:
    try:
        # Generate unique fingerprint for this account
        fingerprint = generate_fingerprint(acc['country'])
        
        # Prepare proxy config
        proxy_config = {
            'host': acc['proxy']['host'],
            'port': acc['proxy']['port'],
            'user': acc['proxy']['user'],
            'password': acc['proxy']['password']
        }
        
        # Add to database
        account_id = add_account(
            username=acc['username'],
            password=acc['password'],
            email=acc['email'],
            email_password=acc['email_password'],
            country_code=acc['country'],
            proxy_config=proxy_config,
            fingerprint=fingerprint
        )
        
        print(f"✅ [{account_id}] {acc['username']} ({acc['country'].upper()})")
        imported += 1
        
    except Exception as e:
        print(f"❌ Failed to import {acc['username']}: {e}")

print("\n" + "=" * 60)
print(f"📊 Imported: {imported}/{len(config['accounts'])} accounts")
print("=" * 60)

# Show summary by country
print("\n📋 Summary by Country:")
accounts = get_all_accounts()

countries = {}
for acc in accounts:
    country = acc['country_code']
    if country not in countries:
        countries[country] = []
    countries[country].append(acc['username'])

for country, usernames in countries.items():
    print(f"\n🌍 {country.upper()} ({len(usernames)} accounts):")
    for u in usernames:
        print(f"   • {u}")
