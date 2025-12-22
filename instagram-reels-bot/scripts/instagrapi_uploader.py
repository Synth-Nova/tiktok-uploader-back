#!/usr/bin/env python3
"""
Instagrapi Reel Uploader
Автоматическая публикация Reels через Instagram Private API (instagrapi)

Преимущества:
- Работает без браузера
- Быстрее чем Selenium
- Поддержка сохранения/загрузки сессий
- Работает с прокси
"""

import os
import sys
import json
import time
import logging
import argparse
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Instagrapi
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, 
    ChallengeRequired, 
    TwoFactorRequired,
    BadPassword,
    PleaseWaitFewMinutes
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "insta_sessions"
VIDEOS_DIR = DATA_DIR / "videos"
LOGS_DIR = BASE_DIR / "logs"

# Create dirs
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Account database
ACCOUNTS = {
    'lourdesparsons20142': {
        'password': 'caewtnwgA!6261',
        'email': 'lourdesparsons2014@hydrofertty.com',
        'country': 'us',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@us.decodo.com:10001'
    },
    'michaelwagner19332': {
        'password': 'ehollwixY!8128',
        'email': 'michaelwagner1933@cryobioltty.com',
        'country': 'us',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@us.decodo.com:10001'
    },
    'phillipjohnson1999': {
        'password': 'mfffmbefY!5255',
        'email': 'phillipjohnson1999@eudiometty.com',
        'country': 'us',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@us.decodo.com:10001'
    },
    'ceciliamotte19001': {
        'password': 'mepwfkhiX!4210',
        'email': 'ceciliamotte1900@duodenojejtty.com',
        'country': 'gb',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@gb.decodo.com:30001'
    },
    'douglasseedorff1944': {
        'password': 'dinfpdwaY!3078',
        'email': 'douglasseedorff1944@leukoctty.com',
        'country': 'gb',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@gb.decodo.com:30001'
    },
    'jameswhite19671': {
        'password': 'rvvfvnzaS!8894',
        'email': 'jameswhite1967@pathophtty.com',
        'country': 'gb',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@gb.decodo.com:30001'
    },
    'arthurlindsay20031': {
        'password': 'ogycwedgY!7232',
        'email': 'arthurlindsay2003@maintaitty.com',
        'country': 'de',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@de.decodo.com:20001'
    },
    'janiethompson19151': {
        'password': 'czuxpdanS!2107',
        'email': 'janiethompson1915@megalosytty.com',
        'country': 'de',
        'proxy': 'http://spvzzn2tmc:gbLZ8rl9y=VlXx37je@de.decodo.com:20001'
    },
}

# Video presets by region
PRESETS = {
    'us': {
        'video': '3_39_m_sub.mp4',
        'caption': '🌙 Daily guidance ✨ What does the universe have for you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing'
    },
    'gb': {
        'video': '3_39_m_en-GB_sub.mp4', 
        'caption': '🌙 Your daily guidance ✨ What message awaits you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing #uk'
    },
    'de': {
        'video': '3_39_m_es-ES_sub.mp4',
        'caption': '🌙 ¿Qué te depara la luna hoy? ✨\n\n#calendariolunar #luna #astrologia #espiritualidad #tarot #manifestacion'
    }
}


class InstagrapiUploader:
    """Instagram Reel uploader using Instagrapi"""
    
    def __init__(self, username: str):
        self.username = username
        self.client = Client()
        self.session_file = SESSIONS_DIR / f"{username}_session.json"
        
        # Get account info
        self.account = ACCOUNTS.get(username)
        if not self.account:
            raise ValueError(f"Account {username} not found in database")
        
        # Configure client
        self._configure_client()
    
    def _configure_client(self):
        """Configure client with anti-detect settings"""
        # Set proxy
        if self.account.get('proxy'):
            self.client.set_proxy(self.account['proxy'])
            logger.info(f"🔌 Proxy set: {self.account['proxy'][:40]}...")
        
        # Set device (random realistic device)
        self.client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 26,
            "android_release": "8.0.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "samsung",
            "device": "SM-G950F",
            "model": "Galaxy S8",
            "cpu": "qcom",
            "version_code": "314665256"
        })
        
        # Set user agent
        self.client.set_user_agent(
            "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; samsung; SM-G950F; dreamlte; qcom; en_US; 314665256)"
        )
        
        # Set country based on account
        country_codes = {'us': 'US', 'gb': 'GB', 'de': 'DE'}
        self.client.set_country(country_codes.get(self.account['country'], 'US'))
        
        # Delay settings (avoid rate limits)
        self.client.delay_range = [1, 3]
    
    def _save_session(self):
        """Save session to file"""
        try:
            settings = self.client.get_settings()
            with open(self.session_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f"✅ Session saved: {self.session_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save session: {e}")
    
    def _load_session(self) -> bool:
        """Load session from file"""
        if not self.session_file.exists():
            return False
        
        try:
            with open(self.session_file, 'r') as f:
                settings = json.load(f)
            self.client.set_settings(settings)
            logger.info(f"✅ Session loaded from file")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to load session: {e}")
            return False
    
    def login(self) -> Tuple[bool, str]:
        """
        Login to Instagram
        
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"🔐 LOGIN: {self.username}")
        logger.info(f"{'='*50}")
        
        # Try loading existing session
        if self._load_session():
            try:
                # Verify session is valid
                self.client.get_timeline_feed()
                logger.info("✅ Session is valid")
                return True, "Logged in via saved session"
            except LoginRequired:
                logger.info("⚠️ Session expired, need fresh login")
            except Exception as e:
                logger.warning(f"⚠️ Session check failed: {e}")
        
        # Fresh login
        try:
            logger.info("🔑 Performing login...")
            
            self.client.login(
                self.username, 
                self.account['password'],
                relogin=True
            )
            
            # Save session
            self._save_session()
            
            logger.info("✅ Login successful!")
            return True, "Login successful"
            
        except BadPassword:
            return False, "Wrong password"
            
        except TwoFactorRequired:
            return False, "2FA required - not supported"
            
        except ChallengeRequired as e:
            logger.warning(f"⚠️ Challenge required: {e}")
            return False, "Challenge/verification required"
            
        except PleaseWaitFewMinutes as e:
            return False, f"Rate limited: {e}"
            
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def upload_reel(
        self, 
        video_path: str, 
        caption: str,
        thumbnail_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Upload a Reel to Instagram
        
        Args:
            video_path: Path to video file (9:16 ratio recommended)
            caption: Caption text with hashtags
            thumbnail_path: Optional thumbnail image
            
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(video_path):
            return False, f"Video not found: {video_path}"
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🎬 UPLOAD REEL: {self.username}")
        logger.info(f"📁 Video: {os.path.basename(video_path)}")
        logger.info(f"{'='*50}")
        
        # Login first
        success, msg = self.login()
        if not success:
            return False, f"Login failed: {msg}"
        
        try:
            logger.info("📤 Uploading reel...")
            
            # Upload reel
            media = self.client.clip_upload(
                path=video_path,
                caption=caption,
                thumbnail=thumbnail_path if thumbnail_path and os.path.exists(thumbnail_path) else None
            )
            
            if media:
                logger.info(f"✅ Reel uploaded!")
                logger.info(f"📎 Media ID: {media.pk}")
                logger.info(f"🔗 URL: https://www.instagram.com/reel/{media.code}/")
                
                # Save upload record
                self._save_upload_record(video_path, caption, media)
                
                return True, f"Reel uploaded! URL: https://www.instagram.com/reel/{media.code}/"
            else:
                return False, "Upload returned no media"
                
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return False, str(e)
    
    def _save_upload_record(self, video_path: str, caption: str, media):
        """Save upload record"""
        record = {
            'username': self.username,
            'video': os.path.basename(video_path),
            'caption': caption[:100] + "...",
            'media_id': str(media.pk),
            'media_code': media.code,
            'url': f"https://www.instagram.com/reel/{media.code}/",
            'timestamp': datetime.now().isoformat()
        }
        
        records_file = LOGS_DIR / "instagrapi_uploads.json"
        
        try:
            records = []
            if records_file.exists():
                with open(records_file, 'r') as f:
                    records = json.load(f)
            
            records.append(record)
            
            with open(records_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to save record: {e}")


def upload_to_account(
    username: str, 
    video_path: str, 
    caption: str
) -> Tuple[bool, str]:
    """Upload reel to specific account"""
    try:
        uploader = InstagrapiUploader(username)
        return uploader.upload_reel(video_path, caption)
    except Exception as e:
        return False, str(e)


def upload_to_region(
    region: str,
    test_mode: bool = False,
    delay: int = 120
) -> Dict[str, List]:
    """Upload to all accounts in a region"""
    
    preset = PRESETS.get(region)
    if not preset:
        logger.error(f"Unknown region: {region}")
        return {'success': [], 'failed': []}
    
    video_path = str(VIDEOS_DIR / preset['video'])
    caption = preset['caption']
    
    # Get accounts for this region
    region_accounts = [
        username for username, data in ACCOUNTS.items() 
        if data['country'] == region
    ]
    
    if test_mode:
        region_accounts = region_accounts[:1]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📍 REGION: {region.upper()}")
    logger.info(f"🎬 Video: {preset['video']}")
    logger.info(f"👥 Accounts: {region_accounts}")
    logger.info(f"{'='*60}")
    
    results = {'success': [], 'failed': []}
    
    for i, username in enumerate(region_accounts):
        logger.info(f"\n[{i+1}/{len(region_accounts)}] {username}")
        
        success, message = upload_to_account(username, video_path, caption)
        
        if success:
            logger.info(f"✅ {username}: {message}")
            results['success'].append({'username': username, 'message': message})
        else:
            logger.error(f"❌ {username}: {message}")
            results['failed'].append({'username': username, 'error': message})
        
        # Delay between accounts
        if i < len(region_accounts) - 1:
            wait = delay + random.randint(-30, 30)
            logger.info(f"⏳ Waiting {wait}s...")
            time.sleep(wait)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Instagrapi Reel Uploader')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show accounts')
    
    # Login test
    login_parser = subparsers.add_parser('login', help='Test login')
    login_parser.add_argument('--account', required=True)
    
    # Upload single
    upload_parser = subparsers.add_parser('upload', help='Upload to account')
    upload_parser.add_argument('--account', required=True)
    upload_parser.add_argument('--video', required=True)
    upload_parser.add_argument('--caption', default='')
    
    # Upload by region
    region_parser = subparsers.add_parser('region', help='Upload to region')
    region_parser.add_argument('--region', required=True, choices=['us', 'gb', 'de'])
    region_parser.add_argument('--test', action='store_true', help='Test mode (1 account only)')
    region_parser.add_argument('--delay', type=int, default=120)
    
    # Upload all
    all_parser = subparsers.add_parser('all', help='Upload to all regions')
    all_parser.add_argument('--test', action='store_true')
    all_parser.add_argument('--delay', type=int, default=120)
    
    args = parser.parse_args()
    
    if args.command == 'status':
        print("\n📊 ACCOUNTS")
        print("="*50)
        for username, data in ACCOUNTS.items():
            session_file = SESSIONS_DIR / f"{username}_session.json"
            has_session = "✅" if session_file.exists() else "❌"
            print(f"{has_session} {username} ({data['country'].upper()})")
        return
    
    elif args.command == 'login':
        uploader = InstagrapiUploader(args.account)
        success, msg = uploader.login()
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: {msg}")
    
    elif args.command == 'upload':
        success, msg = upload_to_account(args.account, args.video, args.caption)
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: {msg}")
    
    elif args.command == 'region':
        results = upload_to_region(args.region, args.test, args.delay)
        print(f"\n📊 RESULTS: ✅ {len(results['success'])} | ❌ {len(results['failed'])}")
    
    elif args.command == 'all':
        all_results = {'success': [], 'failed': []}
        for region in ['us', 'gb', 'de']:
            results = upload_to_region(region, args.test, args.delay)
            all_results['success'].extend(results['success'])
            all_results['failed'].extend(results['failed'])
        print(f"\n📊 TOTAL: ✅ {len(all_results['success'])} | ❌ {len(all_results['failed'])}")
    
    else:
        print("\n🎬 INSTAGRAPI REEL UPLOADER")
        print("="*50)
        print("\nCommands:")
        print("  status              - Show all accounts")
        print("  login --account X   - Test login")
        print("  upload --account X --video PATH --caption TEXT")
        print("  region --region us|gb|de [--test] [--delay 120]")
        print("  all [--test] [--delay 120]")


if __name__ == "__main__":
    main()
