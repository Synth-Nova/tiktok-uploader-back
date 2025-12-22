#!/usr/bin/env python3
"""
Batch Auto Login Script
Автоматический логин всех аккаунтов с сохранением cookies
"""

import sys
import json
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.core.database import get_all_accounts, update_account_cookies, update_account_status
except ImportError:
    # Fallback if database module not available
    get_all_accounts = None
    update_account_cookies = None
    update_account_status = None
    
from src.modules.auto_login import auto_login_account


# Маппинг аккаунтов и GoLogin профилей
ACCOUNTS_CONFIG = [
    {
        'username': 'charleshenry19141',
        'password': 'vujlkedeY!6778',
        'email': 'charleshenry1914@sociobitty.com',
        'email_password': 'vujlkedeY!6778',
        'country': 'de',
        'proxy': {
            'host': 'de.decodo.com',
            'port': 20001,
            'user': 'spvzzn2tmc',
            'password': 'gbLZ8rl9y=VlXx37je'
        }
    },
    {
        'username': 'arthurlindsay20031',
        'password': 'ogycwedgY!7232',
        'email': 'arthurlindsay2003@maintaitty.com',
        'email_password': 'ogycwedgY!7232',
        'country': 'de',
        'proxy': {
            'host': 'de.decodo.com',
            'port': 20002,
            'user': 'spvzzn2tmc',
            'password': 'gbLZ8rl9y=VlXx37je'
        }
    },
    {
        'username': 'janiethompson19151',
        'password': 'czuxpdanS!2107',
        'email': 'janiethompson1915@megalosytty.com',
        'email_password': 'czuxpdanS!2107',
        'country': 'de',
        'proxy': {
            'host': 'de.decodo.com',
            'port': 20003,
            'user': 'spvzzn2tmc',
            'password': 'gbLZ8rl9y=VlXx37je'
        }
    },
    {
        'username': 'ceciliamotte19001',
        'password': 'mepwfkhiX!4210',
        'email': 'ceciliamotte1900@duodenojejtty.com',
        'email_password': 'mepwfkhiX!4210',
        'country': 'gb',
        'proxy': {
            'host': 'gb.decodo.com',
            'port': 30001,
            'user': 'spvzzn2tmc',
            'password': 'gbLZ8rl9y=VlXx37je'
        }
    },
    {
        'username': 'douglasseedorff1944',
        'password': 'dinfpdwaY!3078',
        'email': 'douglasseedorff1944@leukoctty.com',
        'email_password': 'dinfpdwaY!3078',
        'country': 'gb',
        'proxy': {
            'host': 'gb.decodo.com',
            'port': 30002,
            'user': 'spvzzn2tmc',
            'password': 'gbLZ8rl9y=VlXx37je'
        }
    },
]


def batch_login(accounts: list = None, delay_between: int = 30):
    """
    Залогинить несколько аккаунтов автоматически
    """
    if accounts is None:
        accounts = ACCOUNTS_CONFIG
    
    print("\n" + "=" * 60)
    print("🚀 BATCH AUTO LOGIN")
    print("=" * 60)
    print(f"Аккаунтов для логина: {len(accounts)}")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': []
    }
    
    for i, account in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] {account['username']} ({account['country'].upper()})")
        print("-" * 40)
        
        try:
            success, message, cookies = auto_login_account(account, save_cookies=True)
            
            if success:
                results['success'].append(account['username'])
                print(f"✅ {account['username']} — УСПЕХ!")
            else:
                results['failed'].append((account['username'], message))
                print(f"❌ {account['username']} — ОШИБКА: {message}")
                
        except Exception as e:
            results['failed'].append((account['username'], str(e)))
            print(f"❌ {account['username']} — ИСКЛЮЧЕНИЕ: {e}")
        
        # Пауза между аккаунтами
        if i < len(accounts):
            print(f"\n⏳ Пауза {delay_between} секунд перед следующим аккаунтом...")
            time.sleep(delay_between)
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ")
    print("=" * 60)
    print(f"✅ Успешно: {len(results['success'])}/{len(accounts)}")
    print(f"❌ Ошибки: {len(results['failed'])}/{len(accounts)}")
    
    if results['success']:
        print("\n✅ Залогинены:")
        for username in results['success']:
            print(f"   • {username}")
    
    if results['failed']:
        print("\n❌ Не удалось:")
        for username, error in results['failed']:
            print(f"   • {username}: {error}")
    
    # Сохранить отчёт
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(accounts),
        'success': results['success'],
        'failed': [{'username': u, 'error': e} for u, e in results['failed']]
    }
    
    with open('login_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Отчёт сохранён: login_report.json")
    
    return results


def login_single(username: str):
    """Залогинить один аккаунт"""
    account = next((a for a in ACCOUNTS_CONFIG if a['username'] == username), None)
    
    if not account:
        print(f"❌ Аккаунт {username} не найден!")
        return
    
    success, message, cookies = auto_login_account(account)
    
    print(f"\n{'='*60}")
    print(f"Результат: {'✅ УСПЕХ' if success else '❌ ОШИБКА'}")
    print(f"Сообщение: {message}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Auto Login')
    parser.add_argument('--username', '-u', help='Login single account')
    parser.add_argument('--all', '-a', action='store_true', help='Login all accounts')
    parser.add_argument('--delay', '-d', type=int, default=30, help='Delay between accounts')
    
    args = parser.parse_args()
    
    if args.username:
        login_single(args.username)
    elif args.all:
        batch_login(delay_between=args.delay)
    else:
        print("Использование:")
        print("  python batch_auto_login.py --username charleshenry19141")
        print("  python batch_auto_login.py --all")
        print("\nДоступные аккаунты:")
        for acc in ACCOUNTS_CONFIG:
            print(f"  • {acc['username']} ({acc['country'].upper()})")
