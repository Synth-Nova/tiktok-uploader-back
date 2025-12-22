#!/usr/bin/env python3
"""
Automated Reels Posting Script
Автоматический постинг Reels на залогиненные аккаунты

Использует сохранённые cookies для авторизации без прокси
(прокси не нужен - мы уже авторизованы через VNC)
"""

import os
import sys
import json
import time
import pickle
import logging
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
VIDEOS_DIR = DATA_DIR / "videos"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Account configuration with video mapping
ACCOUNTS = {
    # USA accounts -> 3_39_m_sub.mp4 (English)
    'us': {
        'accounts': [
            'lourdesparsons20142',
            'michaelwagner19332', 
            'phillipjohnson1999',
            'rodneysmith19191'  # Not logged in
        ],
        'video': '3_39_m_sub.mp4',
        'caption': '🌙 Daily guidance ✨ What does the universe have for you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing'
    },
    # UK accounts -> 3_39_m_en-GB_sub.mp4 (British English)  
    'gb': {
        'accounts': [
            'ceciliamotte19001',
            'douglasseedorff1944',
            'jameswhite19671'
        ],
        'video': '3_39_m_en-GB_sub.mp4',
        'caption': '🌙 Your daily guidance ✨ What message awaits you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing #uk'
    },
    # Germany accounts -> 3_39_m_es-ES_sub.mp4 (Spanish subtitles for DE region)
    'de': {
        'accounts': [
            'charleshenry19141',  # Not logged in (check)
            'arthurlindsay20031',
            'janiethompson19151'
        ],
        'video': '3_39_m_es-ES_sub.mp4',
        'caption': '🌙 ¿Qué te depara la luna hoy? ✨\n\n#calendariolunar #luna #astrologia #espiritualidad #tarot #manifestacion'
    }
}


class ReelsAutoPoster:
    """Automated Reels Poster using saved cookies"""
    
    INSTAGRAM_BASE_URL = "https://www.instagram.com/"
    
    def __init__(self, username: str, country: str = 'us', headless: bool = True):
        self.username = username
        self.country = country
        self.headless = headless
        self.driver = None
        self.cookies = None
    
    def _get_cookies_path(self) -> Path:
        return SESSIONS_DIR / f"{self.username}_cookies.pkl"
    
    def _load_cookies(self) -> bool:
        """Load saved cookies"""
        cookies_path = self._get_cookies_path()
        if cookies_path.exists():
            try:
                with open(cookies_path, 'rb') as f:
                    self.cookies = pickle.load(f)
                logger.info(f"✅ Loaded {len(self.cookies)} cookies for {self.username}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to load cookies: {e}")
        return False
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with anti-detect"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # Anti-detect
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Realistic user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        options.add_argument("--lang=en-US")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        
        # Anti-detect CDP
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            '''
        })
        
        return driver
    
    def _apply_cookies(self) -> bool:
        """Apply cookies to driver"""
        if not self.cookies or not self.driver:
            return False
        
        try:
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(2)
            
            for cookie in self.cookies:
                try:
                    if 'sameSite' in cookie:
                        if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'Lax'
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"❌ Cookie error: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        try:
            time.sleep(3)
            page_source = self.driver.page_source.lower()
            
            # Check for logged in indicators
            if 'create' in page_source and ('home' in page_source or 'direct' in page_source):
                return True
            
            if 'log in' in page_source or 'sign up' in page_source:
                return False
            
            # Try finding create button
            try:
                self.driver.find_element(By.XPATH, "//*[contains(@aria-label, 'New post') or contains(@aria-label, 'Create')]")
                return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.error(f"❌ Login check error: {e}")
            return False
    
    def upload_reel(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """Upload a Reel to Instagram"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 UPLOADING REEL: {self.username}")
        logger.info(f"📁 Video: {video_path}")
        logger.info(f"{'='*60}")
        
        if not os.path.exists(video_path):
            return False, f"Video not found: {video_path}"
        
        video_path = os.path.abspath(video_path)
        
        try:
            # Load cookies
            if not self._load_cookies():
                return False, "No cookies found - account not logged in"
            
            # Setup driver
            logger.info("🌐 Starting browser...")
            self.driver = self._setup_driver()
            
            # Apply cookies
            if not self._apply_cookies():
                return False, "Failed to apply cookies"
            
            # Refresh and check
            self.driver.refresh()
            time.sleep(3)
            
            if not self._is_logged_in():
                return False, "Not logged in - cookies may have expired"
            
            logger.info("✅ Successfully logged in via cookies")
            
            # Try to upload
            return self._do_upload(video_path, caption)
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False, str(e)
        finally:
            if self.driver:
                try:
                    # Screenshot
                    screenshot_path = LOGS_DIR / f"{self.username}_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    logger.info(f"📸 Screenshot: {screenshot_path}")
                except:
                    pass
                self.driver.quit()
    
    def _do_upload(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """Perform the actual upload"""
        try:
            # Go to Instagram home
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(3)
            
            # Find Create button
            logger.info("🔍 Looking for Create button...")
            
            create_btn = None
            selectors = [
                "//*[@aria-label='New post']",
                "//*[@aria-label='Create']",
                "//svg[@aria-label='New post']/parent::*",
                "//span[text()='Create']/ancestor::*[@role='link']",
                "//a[contains(@href, '/create/')]"
            ]
            
            for sel in selectors:
                try:
                    create_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, sel))
                    )
                    if create_btn:
                        break
                except:
                    continue
            
            if not create_btn:
                # Try CSS
                css_selectors = [
                    "[aria-label='New post']",
                    "[aria-label='Create']",
                    "a[href*='create']"
                ]
                for sel in css_selectors:
                    try:
                        create_btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                        break
                    except:
                        continue
            
            if not create_btn:
                return False, "Could not find Create button"
            
            logger.info("✅ Found Create button, clicking...")
            create_btn.click()
            time.sleep(3)
            
            # Find file input
            logger.info("🔍 Looking for file input...")
            file_input = None
            
            try:
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except:
                # Click "Select from computer" if visible
                try:
                    select_btn = self.driver.find_element(By.XPATH, 
                        "//button[contains(text(), 'Select from computer') or contains(text(), 'Select')]"
                    )
                    select_btn.click()
                    time.sleep(1)
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                except:
                    pass
            
            if not file_input:
                return False, "Could not find file input"
            
            # Upload
            logger.info(f"📤 Uploading video...")
            file_input.send_keys(video_path)
            
            # Wait for processing
            logger.info("⏳ Processing video (30 sec)...")
            time.sleep(30)
            
            # Click through Next buttons
            logger.info("⏭️ Navigating through wizard...")
            for i in range(3):
                try:
                    next_btn = self.driver.find_element(By.XPATH, 
                        "//button[contains(text(), 'Next')]|//div[text()='Next']/ancestor::button"
                    )
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(2)
                except:
                    pass
            
            # Add caption
            logger.info("✏️ Adding caption...")
            try:
                caption_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//textarea[@aria-label='Write a caption...' or contains(@placeholder, 'caption')]"
                    ))
                )
                caption_input.click()
                time.sleep(0.5)
                
                # Type caption
                for char in caption:
                    caption_input.send_keys(char)
                    time.sleep(0.01)
                
                logger.info("✅ Caption added")
            except Exception as e:
                logger.warning(f"⚠️ Caption error: {e}")
            
            time.sleep(2)
            
            # Click Share
            logger.info("🚀 Sharing reel...")
            try:
                share_btn = self.driver.find_element(By.XPATH,
                    "//button[contains(text(), 'Share')]|//div[text()='Share']/ancestor::button"
                )
                share_btn.click()
            except:
                # Try alternative
                try:
                    share_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Post')]")
                    share_btn.click()
                except:
                    pass
            
            # Wait for upload
            logger.info("⏳ Waiting for upload to complete (60 sec)...")
            time.sleep(60)
            
            # Check success
            page_source = self.driver.page_source.lower()
            if 'your reel has been shared' in page_source or 'shared' in page_source:
                return True, "Reel uploaded successfully!"
            
            return True, "Upload initiated - check Instagram for confirmation"
            
        except Exception as e:
            return False, str(e)


def get_logged_in_accounts() -> Dict[str, List[str]]:
    """Get list of accounts with valid cookies"""
    logged_in = {'us': [], 'gb': [], 'de': []}
    
    for region, data in ACCOUNTS.items():
        for username in data['accounts']:
            cookie_file = SESSIONS_DIR / f"{username}_cookies.pkl"
            if cookie_file.exists():
                logged_in[region].append(username)
    
    return logged_in


def run_auto_posting(
    regions: List[str] = None,
    delay_between_accounts: int = 120,
    test_mode: bool = False
):
    """
    Run automated posting to all logged-in accounts
    
    Args:
        regions: List of regions to post to (None = all)
        delay_between_accounts: Seconds between each account post
        test_mode: If True, only post to first account per region
    """
    logger.info("\n" + "="*70)
    logger.info("🚀 AUTOMATED REELS POSTING STARTED")
    logger.info("="*70 + "\n")
    
    logged_in = get_logged_in_accounts()
    
    total_logged_in = sum(len(accs) for accs in logged_in.values())
    logger.info(f"📊 Found {total_logged_in} logged-in accounts")
    
    for region, accounts in logged_in.items():
        logger.info(f"   {region.upper()}: {len(accounts)} accounts")
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    regions_to_process = regions or ['us', 'gb', 'de']
    
    for region in regions_to_process:
        if region not in ACCOUNTS:
            continue
        
        region_data = ACCOUNTS[region]
        video_file = region_data['video']
        caption = region_data['caption']
        accounts = logged_in.get(region, [])
        
        if not accounts:
            logger.warning(f"⚠️ No logged-in accounts for region {region.upper()}")
            continue
        
        video_path = VIDEOS_DIR / video_file
        if not video_path.exists():
            logger.error(f"❌ Video not found: {video_path}")
            results['failed'].append({
                'region': region,
                'error': f'Video not found: {video_file}'
            })
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📍 REGION: {region.upper()}")
        logger.info(f"🎬 Video: {video_file}")
        logger.info(f"👥 Accounts: {len(accounts)}")
        logger.info(f"{'='*60}")
        
        accounts_to_process = accounts[:1] if test_mode else accounts
        
        for i, username in enumerate(accounts_to_process):
            logger.info(f"\n[{i+1}/{len(accounts_to_process)}] Account: {username}")
            
            try:
                poster = ReelsAutoPoster(
                    username=username,
                    country=region,
                    headless=True
                )
                
                success, message = poster.upload_reel(
                    str(video_path),
                    caption
                )
                
                if success:
                    logger.info(f"✅ SUCCESS: {username} - {message}")
                    results['success'].append({
                        'username': username,
                        'region': region,
                        'message': message
                    })
                else:
                    logger.error(f"❌ FAILED: {username} - {message}")
                    results['failed'].append({
                        'username': username,
                        'region': region,
                        'error': message
                    })
                
            except Exception as e:
                logger.error(f"❌ EXCEPTION: {username} - {e}")
                results['failed'].append({
                    'username': username,
                    'region': region,
                    'error': str(e)
                })
            
            # Delay between accounts
            if i < len(accounts_to_process) - 1:
                delay = delay_between_accounts + random.randint(-30, 30)
                logger.info(f"⏳ Waiting {delay} seconds before next account...")
                time.sleep(delay)
    
    # Print summary
    logger.info("\n" + "="*70)
    logger.info("📊 POSTING SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Successful: {len(results['success'])}")
    logger.info(f"❌ Failed: {len(results['failed'])}")
    logger.info(f"⏭️ Skipped: {len(results['skipped'])}")
    
    if results['success']:
        logger.info("\n✅ Successfully posted to:")
        for r in results['success']:
            logger.info(f"   - {r['username']} ({r['region'].upper()})")
    
    if results['failed']:
        logger.info("\n❌ Failed accounts:")
        for r in results['failed']:
            logger.info(f"   - {r.get('username', 'N/A')} ({r.get('region', 'N/A').upper()}): {r['error']}")
    
    # Save report
    report_file = LOGS_DIR / f"posting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"\n📄 Report saved: {report_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Automated Reels Posting')
    parser.add_argument('--mode', choices=['status', 'post', 'test'], default='status',
                        help='Mode: status (check accounts), post (upload to all), test (upload to one per region)')
    parser.add_argument('--regions', nargs='+', choices=['us', 'gb', 'de'],
                        help='Specific regions to process')
    parser.add_argument('--delay', type=int, default=120,
                        help='Delay between accounts in seconds (default: 120)')
    
    args = parser.parse_args()
    
    if args.mode == 'status':
        logger.info("\n📊 ACCOUNT STATUS")
        logger.info("="*50)
        
        logged_in = get_logged_in_accounts()
        total = 0
        
        for region, accounts in logged_in.items():
            total += len(accounts)
            logger.info(f"\n{region.upper()} ({len(accounts)} accounts):")
            for acc in accounts:
                logger.info(f"   ✅ {acc}")
            
            # Show not logged in
            all_accs = ACCOUNTS[region]['accounts']
            for acc in all_accs:
                if acc not in accounts:
                    logger.info(f"   ❌ {acc} (not logged in)")
        
        logger.info(f"\n📊 Total logged in: {total}")
        
    elif args.mode == 'test':
        logger.info("🧪 TEST MODE - Uploading to one account per region")
        run_auto_posting(
            regions=args.regions,
            delay_between_accounts=args.delay,
            test_mode=True
        )
        
    elif args.mode == 'post':
        logger.info("🚀 POSTING MODE - Uploading to all accounts")
        run_auto_posting(
            regions=args.regions,
            delay_between_accounts=args.delay,
            test_mode=False
        )


if __name__ == "__main__":
    main()
