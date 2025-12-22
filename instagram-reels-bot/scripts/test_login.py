#!/usr/bin/env python3
"""
Test Instagram Login Script
Tests login for a single account with proxy and anti-detect
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_account, update_account_status, update_account_cookies
from src.modules.instagram_auth import InstagramAuth
from src.modules.email_parser import get_email_parser
from src.utils.fingerprint_generator import generate_fingerprint


def test_single_login(account_id: int = 1, headless: bool = False):
    """Test login for a single account"""
    
    # Get account from database
    account = get_account(account_id)
    
    if not account:
        print(f"❌ Account ID {account_id} not found in database")
        return False
    
    print("\n" + "=" * 60)
    print("🧪 Instagram Login Test")
    print("=" * 60)
    print(f"Account ID: {account['id']}")
    print(f"Username: {account['username']}")
    print(f"Country: {account['country_code'].upper()}")
    print(f"Proxy: {account['proxy_host']}:{account['proxy_port']}")
    print(f"Status: {account['status']}")
    print("=" * 60)
    
    # Prepare proxy config
    proxy = {
        'host': account['proxy_host'],
        'port': account['proxy_port'],
        'user': account['proxy_user'],
        'password': account['proxy_pass']
    }
    
    # Get or generate fingerprint
    if account['fingerprint']:
        fingerprint = json.loads(account['fingerprint'])
    else:
        fingerprint = generate_fingerprint(account['country_code'])
    
    print(f"\n📱 Fingerprint:")
    print(f"   Platform: {fingerprint.get('platform')}")
    print(f"   Language: {fingerprint.get('language')}")
    print(f"   Timezone: {fingerprint.get('timezone')}")
    print(f"   Screen: {fingerprint.get('screenWidth')}x{fingerprint.get('screenHeight')}")
    
    # Create auth instance
    auth = InstagramAuth(
        username=account['username'],
        password=account['password'],
        proxy=proxy,
        fingerprint=fingerprint,
        headless=headless
    )
    
    try:
        # Attempt login
        print("\n🔐 Starting login process...")
        success, message = auth.login()
        
        print("\n" + "=" * 60)
        print("📊 RESULT:")
        print("=" * 60)
        
        if success:
            print("✅ LOGIN SUCCESSFUL!")
            
            # Save cookies
            cookies = auth.get_cookies()
            print(f"🍪 Cookies saved: {len(cookies)} cookies")
            
            # Update database
            update_account_cookies(account['id'], cookies)
            update_account_status(account['id'], 'active', 'Login successful')
            
            print("💾 Database updated")
            return True
            
        else:
            print(f"❌ LOGIN FAILED: {message}")
            
            # Handle different failure types
            if message == "2FA_REQUIRED":
                print("\n🔐 Two-Factor Authentication required!")
                print("   Need to handle 2FA verification")
                update_account_status(account['id'], 'needs_2fa', message)
                
            elif message == "EMAIL_VERIFICATION_REQUIRED":
                print("\n📧 Email verification required!")
                print("   Attempting to get verification code...")
                
                # Try to get email code
                parser = get_email_parser(account['email'], account['email_password'])
                code = parser.get_verification_code(timeout_seconds=60)
                
                if code:
                    print(f"✅ Got verification code: {code}")
                    # TODO: Enter code and retry login
                else:
                    print("❌ Could not get verification code")
                    
                update_account_status(account['id'], 'needs_email_verify', message)
                
            elif message == "SUSPICIOUS_LOGIN":
                print("\n⚠️ Suspicious login activity detected!")
                print("   Account may need manual verification")
                update_account_status(account['id'], 'suspicious', message)
                
            elif message == "WRONG_PASSWORD":
                print("\n❌ Wrong password!")
                update_account_status(account['id'], 'wrong_password', message)
                
            elif message == "ACCOUNT_DISABLED":
                print("\n🚫 Account is disabled/banned!")
                update_account_status(account['id'], 'banned', message)
                
            else:
                update_account_status(account['id'], 'error', message)
            
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        update_account_status(account['id'], 'error', str(e))
        return False
        
    finally:
        if not headless:
            input("\n⏎ Press Enter to close browser...")
        auth.close()


def test_all_accounts(headless: bool = True, delay: int = 30):
    """Test login for all accounts"""
    from src.core.database import get_all_accounts
    import time
    
    accounts = get_all_accounts()
    
    print("\n" + "=" * 60)
    print(f"🧪 Testing {len(accounts)} accounts")
    print("=" * 60)
    
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for i, account in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Testing {account['username']}...")
        
        try:
            success = test_single_login(account['id'], headless=headless)
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(account['username'])
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{account['username']}: {e}")
        
        # Delay between accounts
        if i < len(accounts):
            print(f"\n⏳ Waiting {delay} seconds before next account...")
            time.sleep(delay)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {results['success']}/{len(accounts)}")
    print(f"❌ Failed: {results['failed']}/{len(accounts)}")
    
    if results['errors']:
        print("\n❌ Failed accounts:")
        for err in results['errors']:
            print(f"   • {err}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Instagram Login')
    parser.add_argument('--account', '-a', type=int, default=1, help='Account ID to test')
    parser.add_argument('--all', action='store_true', help='Test all accounts')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--delay', type=int, default=30, help='Delay between accounts (seconds)')
    
    args = parser.parse_args()
    
    if args.all:
        test_all_accounts(headless=args.headless, delay=args.delay)
    else:
        test_single_login(account_id=args.account, headless=args.headless)
