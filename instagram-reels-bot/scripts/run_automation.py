#!/usr/bin/env python3
"""
Instagram Reels Automation Runner
Полная автоматизация: логин → загрузка видео → мониторинг

Использование:
    python run_automation.py --mode login-all     # Залогинить все аккаунты
    python run_automation.py --mode upload        # Загрузить видео
    python run_automation.py --mode test          # Тест одного аккаунта
"""

import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.auto_login import auto_login_account, InstagramAutoLogin
from src.modules.reels_uploader import upload_reel_to_account, ReelsUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== CONFIGURATION ==============

# Все 10 аккаунтов с прокси
ACCOUNTS_CONFIG = [
    # USA Accounts (4)
    {
        'username': 'lourdesparsons20142',
        'password': 'caewtnwgA!6261',
        'email': 'lourdesparsons2014@hydrofertty.com',
        'email_password': 'caewtnwgA!6261',
        'country': 'us',
        'proxy': {'host': 'us.decodo.com', 'port': 10001, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_sub.mp4'  # USA video
    },
    {
        'username': 'michaelwagner19332',
        'password': 'ehollwixY!8128',
        'email': 'michaelwagner1933@cryobioltty.com',
        'email_password': 'ehollwixY!8128',
        'country': 'us',
        'proxy': {'host': 'us.decodo.com', 'port': 10002, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_sub.mp4'
    },
    {
        'username': 'phillipjohnson1999',
        'password': 'mfffmbefY!5255',
        'email': 'phillipjohnson1999@eudiometty.com',
        'email_password': 'mfffmbefY!5255',
        'country': 'us',
        'proxy': {'host': 'us.decodo.com', 'port': 10003, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_sub.mp4'
    },
    {
        'username': 'rodneysmith19191',
        'password': 'asbvcvvmY!6131',
        'email': 'rodneysmith1919@neocolotty.com',
        'email_password': 'asbvcvvmY!6131',
        'country': 'us',
        'proxy': {'host': 'us.decodo.com', 'port': 10004, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_sub.mp4'
    },
    
    # UK Accounts (3)
    {
        'username': 'ceciliamotte19001',
        'password': 'mepwfkhiX!4210',
        'email': 'ceciliamotte1900@duodenojejtty.com',
        'email_password': 'mepwfkhiX!4210',
        'country': 'gb',
        'proxy': {'host': 'gb.decodo.com', 'port': 30001, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_en-GB_sub.mp4'  # UK video
    },
    {
        'username': 'douglasseedorff1944',
        'password': 'dinfpdwaY!3078',
        'email': 'douglasseedorff1944@leukoctty.com',
        'email_password': 'dinfpdwaY!3078',
        'country': 'gb',
        'proxy': {'host': 'gb.decodo.com', 'port': 30002, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_en-GB_sub.mp4'
    },
    {
        'username': 'jameswhite19671',
        'password': 'rvvfvnzaS!8894',
        'email': 'jameswhite1967@pathophtty.com',
        'email_password': 'rvvfvnzaS!8894',
        'country': 'gb',
        'proxy': {'host': 'gb.decodo.com', 'port': 30003, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_en-GB_sub.mp4'
    },
    
    # Germany Accounts (3)
    {
        'username': 'charleshenry19141',
        'password': 'vujlkedeY!6778',
        'email': 'charleshenry1914@sociobitty.com',
        'email_password': 'vujlkedeY!6778',
        'country': 'de',
        'proxy': {'host': 'de.decodo.com', 'port': 20001, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_es-ES_sub.mp4'  # TODO: Replace with de-DE video
    },
    {
        'username': 'arthurlindsay20031',
        'password': 'ogycwedgY!7232',
        'email': 'arthurlindsay2003@maintaitty.com',
        'email_password': 'ogycwedgY!7232',
        'country': 'de',
        'proxy': {'host': 'de.decodo.com', 'port': 20002, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_es-ES_sub.mp4'
    },
    {
        'username': 'janiethompson19151',
        'password': 'czuxpdanS!2107',
        'email': 'janiethompson1915@megalosytty.com',
        'email_password': 'czuxpdanS!2107',
        'country': 'de',
        'proxy': {'host': 'de.decodo.com', 'port': 20003, 'user': 'spvzzn2tmc', 'password': 'gbLZ8rl9y=VlXx37je'},
        'video': '3_39_m_es-ES_sub.mp4'
    },
]

# Videos directory (to be configured)
VIDEOS_DIR = Path(__file__).parent.parent / "data" / "videos"

# Default captions per country
CAPTIONS = {
    'us': "✨ Daily guidance ✨ #tarot #spirituality #guidance #dailytarot",
    'gb': "✨ Daily guidance ✨ #tarot #spirituality #guidance #uk #dailytarot",
    'de': "✨ Tägliche Führung ✨ #tarot #spiritualität #führung #deutschland",
}


# ============== FUNCTIONS ==============

def login_all_accounts(accounts: List[Dict] = None, delay: int = 60) -> Dict:
    """
    Залогинить все аккаунты
    """
    accounts = accounts or ACCOUNTS_CONFIG
    
    logger.info("\n" + "="*60)
    logger.info("🚀 BATCH LOGIN - All Accounts")
    logger.info("="*60)
    logger.info(f"Total accounts: {len(accounts)}")
    logger.info(f"Delay between: {delay}s")
    logger.info("="*60)
    
    results = {'success': [], 'failed': []}
    
    for i, account in enumerate(accounts, 1):
        logger.info(f"\n[{i}/{len(accounts)}] {account['username']} ({account['country'].upper()})")
        logger.info("-" * 40)
        
        try:
            success, message, cookies = auto_login_account(account)
            
            if success:
                results['success'].append(account['username'])
                logger.info(f"✅ {account['username']} - SUCCESS")
            else:
                results['failed'].append((account['username'], message))
                logger.info(f"❌ {account['username']} - FAILED: {message}")
                
        except Exception as e:
            results['failed'].append((account['username'], str(e)))
            logger.error(f"❌ {account['username']} - ERROR: {e}")
        
        # Delay between logins (avoid rate limits)
        if i < len(accounts):
            logger.info(f"\n⏳ Waiting {delay}s before next account...")
            time.sleep(delay)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 LOGIN SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Success: {len(results['success'])}/{len(accounts)}")
    logger.info(f"❌ Failed: {len(results['failed'])}/{len(accounts)}")
    
    if results['success']:
        logger.info("\n✅ Logged in:")
        for username in results['success']:
            logger.info(f"   • {username}")
    
    if results['failed']:
        logger.info("\n❌ Failed:")
        for username, error in results['failed']:
            logger.info(f"   • {username}: {error}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total': len(accounts),
        'success': results['success'],
        'failed': [{'username': u, 'error': e} for u, e in results['failed']]
    }
    
    report_path = Path(__file__).parent.parent / "data" / "login_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\n📄 Report saved: {report_path}")
    
    return results


def upload_to_all_accounts(video_dir: str = None, accounts: List[Dict] = None, delay: int = 120) -> Dict:
    """
    Загрузить видео на все аккаунты
    """
    accounts = accounts or ACCOUNTS_CONFIG
    video_dir = Path(video_dir) if video_dir else VIDEOS_DIR
    
    logger.info("\n" + "="*60)
    logger.info("🎬 BATCH UPLOAD - All Accounts")
    logger.info("="*60)
    logger.info(f"Total accounts: {len(accounts)}")
    logger.info(f"Videos dir: {video_dir}")
    logger.info("="*60)
    
    results = {'success': [], 'failed': []}
    
    for i, account in enumerate(accounts, 1):
        username = account['username']
        country = account['country']
        video_file = account.get('video', f"video_{country}.mp4")
        video_path = video_dir / video_file
        
        logger.info(f"\n[{i}/{len(accounts)}] {username} ({country.upper()})")
        logger.info(f"Video: {video_file}")
        logger.info("-" * 40)
        
        # Check video exists
        if not video_path.exists():
            logger.warning(f"⚠️ Video not found: {video_path}")
            results['failed'].append((username, "Video not found"))
            continue
        
        try:
            success, message = upload_reel_to_account(
                username=username,
                video_path=str(video_path),
                caption=CAPTIONS.get(country, "✨ Daily guidance ✨"),
                hashtags=None,  # Already in caption
                proxy=account.get('proxy'),
                country=country,
                headless=True
            )
            
            if success:
                results['success'].append(username)
                logger.info(f"✅ {username} - UPLOADED")
            else:
                results['failed'].append((username, message))
                logger.info(f"❌ {username} - FAILED: {message}")
                
        except Exception as e:
            results['failed'].append((username, str(e)))
            logger.error(f"❌ {username} - ERROR: {e}")
        
        # Delay between uploads
        if i < len(accounts):
            logger.info(f"\n⏳ Waiting {delay}s before next upload...")
            time.sleep(delay)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 UPLOAD SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Success: {len(results['success'])}/{len(accounts)}")
    logger.info(f"❌ Failed: {len(results['failed'])}/{len(accounts)}")
    
    return results


def test_single_account(username: str = None):
    """
    Тест одного аккаунта
    """
    # Find account
    if username:
        account = next((a for a in ACCOUNTS_CONFIG if a['username'] == username), None)
    else:
        account = ACCOUNTS_CONFIG[0]  # First account
    
    if not account:
        logger.error(f"Account not found: {username}")
        return
    
    logger.info("\n" + "="*60)
    logger.info(f"🧪 TEST: {account['username']}")
    logger.info("="*60)
    
    # Test login
    logger.info("\n📝 Step 1: Testing login...")
    success, message, cookies = auto_login_account(account)
    
    logger.info(f"Login result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    logger.info(f"Message: {message}")
    
    if success and cookies:
        logger.info(f"Cookies saved: {len(cookies)} items")
    
    return success


def show_status():
    """Show current account status"""
    logger.info("\n" + "="*60)
    logger.info("📊 ACCOUNT STATUS")
    logger.info("="*60)
    
    sessions_dir = Path(__file__).parent.parent / "data" / "sessions"
    
    for account in ACCOUNTS_CONFIG:
        username = account['username']
        country = account['country'].upper()
        
        cookies_file = sessions_dir / f"{username}_cookies.pkl"
        session_file = sessions_dir / f"{username}_session.json"
        
        status = "❌ Not logged in"
        if cookies_file.exists():
            if session_file.exists():
                try:
                    with open(session_file, 'r') as f:
                        session = json.load(f)
                    saved_at = session.get('saved_at', 'unknown')
                    status = f"✅ Logged in ({saved_at[:10]})"
                except:
                    status = "✅ Cookies exist"
            else:
                status = "✅ Cookies exist"
        
        logger.info(f"{country} | {username[:20]:<20} | {status}")


def main():
    parser = argparse.ArgumentParser(description='Instagram Reels Automation')
    parser.add_argument('--mode', '-m', 
                        choices=['login-all', 'upload', 'test', 'status'],
                        default='status',
                        help='Режим работы')
    parser.add_argument('--username', '-u', help='Username для теста')
    parser.add_argument('--video-dir', '-v', help='Директория с видео')
    parser.add_argument('--delay', '-d', type=int, default=60, help='Задержка между аккаунтами')
    
    args = parser.parse_args()
    
    if args.mode == 'login-all':
        login_all_accounts(delay=args.delay)
    elif args.mode == 'upload':
        upload_to_all_accounts(video_dir=args.video_dir, delay=args.delay)
    elif args.mode == 'test':
        test_single_account(args.username)
    elif args.mode == 'status':
        show_status()


if __name__ == "__main__":
    main()
