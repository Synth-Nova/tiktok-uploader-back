#!/usr/bin/env python3
"""
Simple Reel Uploader - Clean profile with manual cookie import
Использует чистый профиль и импортирует cookies из файлов
"""

import os
import sys
import time
import pickle
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "data" / "sessions"
VIDEOS_DIR = BASE_DIR / "data" / "videos"
LOGS_DIR = BASE_DIR / "logs"
PROFILES_DIR = BASE_DIR / "chrome_profiles"

# Ensure directories
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


class SimpleReelUploader:
    """
    Simple Reel Uploader using VNC display and cookies
    """
    
    def __init__(self, username: str, country: str = 'us'):
        self.username = username
        self.country = country
        self.driver = None
        
        # Profile directory for this user
        self.profile_dir = PROFILES_DIR / username
        self.profile_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cookies_path(self) -> Path:
        return SESSIONS_DIR / f"{self.username}_cookies.pkl"
    
    def _load_cookies(self) -> list:
        """Load cookies from pickle file"""
        path = self._get_cookies_path()
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    cookies = pickle.load(f)
                logger.info(f"✅ Loaded {len(cookies)} cookies")
                return cookies
            except Exception as e:
                logger.error(f"❌ Cookie load error: {e}")
        return []
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver"""
        # Kill any existing Chrome to prevent profile lock
        subprocess.run(['pkill', '-9', '-f', 'chrome'], capture_output=True)
        time.sleep(2)
        
        # Set display
        os.environ['DISPLAY'] = ':1'
        
        options = Options()
        
        # Use separate profile per user (prevents conflicts)
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        
        # Basic stability options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        
        # Anti-detect
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Window
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        
        # User agent
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={ua}")
        
        driver = webdriver.Chrome(options=options)
        
        # Anti-detect JS
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            '''
        })
        
        driver.maximize_window()
        return driver
    
    def _apply_cookies(self, cookies: list) -> bool:
        """Apply cookies to current session"""
        if not cookies:
            return False
        
        try:
            # Navigate to Instagram first (required for domain)
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            added = 0
            for cookie in cookies:
                try:
                    # Fix sameSite
                    if 'sameSite' in cookie:
                        if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'Lax'
                    
                    # Fix domain
                    if 'domain' not in cookie:
                        cookie['domain'] = '.instagram.com'
                    
                    self.driver.add_cookie(cookie)
                    added += 1
                except Exception as e:
                    pass
            
            logger.info(f"✅ Applied {added}/{len(cookies)} cookies")
            return added > 0
            
        except Exception as e:
            logger.error(f"❌ Apply cookies error: {e}")
            return False
    
    def _check_logged_in(self) -> bool:
        """Check if logged into Instagram"""
        try:
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(4)
            
            # Check for login page indicators
            page = self.driver.page_source.lower()
            url = self.driver.current_url
            
            # Not logged in indicators
            if 'accounts/login' in url:
                return False
            
            try:
                login_input = self.driver.find_element(By.NAME, 'username')
                if login_input.is_displayed():
                    return False
            except:
                pass
            
            # Logged in indicators
            if 'create' in page and ('home' in page or 'feed' in page):
                return True
            
            # Try finding profile/create elements
            for sel in ["//*[@aria-label='New post']", "//*[@aria-label='Create']"]:
                try:
                    elem = self.driver.find_element(By.XPATH, sel)
                    if elem.is_displayed():
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.error(f"Login check error: {e}")
            return False
    
    def upload_reel(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """
        Upload a Reel to Instagram
        """
        if not os.path.exists(video_path):
            return False, f"Video not found: {video_path}"
        
        video_path = os.path.abspath(video_path)
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎬 UPLOADING REEL")
            logger.info(f"👤 Account: {self.username}")
            logger.info(f"📁 Video: {os.path.basename(video_path)}")
            logger.info(f"{'='*60}")
            
            # Load cookies
            cookies = self._load_cookies()
            if not cookies:
                return False, "No cookies found - login via VNC first"
            
            # Setup driver
            logger.info("🌐 Starting Chrome...")
            self.driver = self._setup_driver()
            
            # Apply cookies
            logger.info("🍪 Applying cookies...")
            if not self._apply_cookies(cookies):
                return False, "Failed to apply cookies"
            
            # Check login
            logger.info("🔐 Checking login status...")
            if not self._check_logged_in():
                # Take screenshot
                self._screenshot("not_logged_in")
                return False, "Not logged in - cookies may be expired, re-login via VNC"
            
            logger.info("✅ Logged in successfully!")
            
            # Do upload
            return self._upload(video_path, caption)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self._screenshot("error")
            return False, str(e)
            
        finally:
            if self.driver:
                try:
                    self._screenshot("final")
                except:
                    pass
                # Leave browser open for debugging
                logger.info("ℹ️ Browser left open")
    
    def _screenshot(self, name: str):
        """Save screenshot"""
        try:
            path = LOGS_DIR / f"{self.username}_{name}_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(str(path))
            logger.info(f"📸 Screenshot: {path}")
        except:
            pass
    
    def _upload(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """Perform the upload"""
        
        # Step 1: Click Create
        logger.info("\n📌 Step 1: Finding Create button...")
        
        create_btn = None
        for sel in ["//*[@aria-label='New post']", "//*[@aria-label='Create']", "//a[contains(@href,'create')]"]:
            try:
                elements = self.driver.find_elements(By.XPATH, sel)
                for e in elements:
                    if e.is_displayed():
                        create_btn = e
                        break
                if create_btn:
                    break
            except:
                pass
        
        if not create_btn:
            self._screenshot("no_create")
            return False, "Create button not found"
        
        logger.info("   Clicking Create...")
        ActionChains(self.driver).move_to_element(create_btn).click().perform()
        time.sleep(4)
        
        # Step 2: Upload file
        logger.info("\n📌 Step 2: Uploading video...")
        
        file_input = None
        try:
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
        except:
            try:
                # Click "Select from computer"
                btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Select')]")
                btn.click()
                time.sleep(2)
                file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            except:
                pass
        
        if not file_input:
            self._screenshot("no_file_input")
            return False, "File input not found"
        
        logger.info(f"   Sending video: {os.path.basename(video_path)}")
        file_input.send_keys(video_path)
        
        # Step 3: Wait for processing
        logger.info("\n📌 Step 3: Processing video...")
        logger.info("   ⏳ Waiting 60 seconds...")
        time.sleep(60)
        
        # Step 4: Navigate through wizard (click Next)
        logger.info("\n📌 Step 4: Wizard navigation...")
        
        for i in range(5):
            try:
                next_btn = self.driver.find_element(By.XPATH, 
                    "//button[.//text()='Next' or text()='Next']|//div[text()='Next']/.."
                )
                if next_btn.is_displayed():
                    ActionChains(self.driver).move_to_element(next_btn).click().perform()
                    logger.info(f"   Clicked Next #{i+1}")
                    time.sleep(3)
            except:
                pass
        
        # Step 5: Add caption
        logger.info("\n📌 Step 5: Adding caption...")
        
        try:
            caption_input = None
            for sel in ["//textarea[@aria-label='Write a caption...']", 
                        "//div[@aria-label='Write a caption...']",
                        "//div[@role='textbox']"]:
                try:
                    elem = self.driver.find_element(By.XPATH, sel)
                    if elem.is_displayed():
                        caption_input = elem
                        break
                except:
                    pass
            
            if caption_input:
                ActionChains(self.driver).move_to_element(caption_input).click().perform()
                time.sleep(0.3)
                for char in caption:
                    caption_input.send_keys(char)
                    time.sleep(0.01)
                logger.info("   ✅ Caption added")
            else:
                logger.warning("   ⚠️ Caption input not found")
        except Exception as e:
            logger.warning(f"   ⚠️ Caption error: {e}")
        
        time.sleep(2)
        
        # Step 6: Share
        logger.info("\n📌 Step 6: Sharing...")
        
        try:
            share_btn = self.driver.find_element(By.XPATH,
                "//button[.//text()='Share' or text()='Share']|//div[text()='Share']/.."
            )
            ActionChains(self.driver).move_to_element(share_btn).click().perform()
            logger.info("   ✅ Clicked Share")
        except:
            logger.warning("   ⚠️ Share button not found")
        
        # Step 7: Wait
        logger.info("\n📌 Step 7: Waiting for upload...")
        logger.info("   ⏳ Waiting 120 seconds...")
        time.sleep(120)
        
        # Check result
        page = self.driver.page_source.lower()
        if 'your reel has been shared' in page or 'shared' in page:
            return True, "🎉 Reel uploaded successfully!"
        
        return True, "Upload initiated - check Instagram"


def main():
    parser = argparse.ArgumentParser(description='Simple Reel Uploader')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a reel')
    upload_parser.add_argument('--account', required=True, help='Account username')
    upload_parser.add_argument('--video', required=True, help='Video file path')
    upload_parser.add_argument('--caption', default='', help='Caption text')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check account status')
    
    # Preset command (easy upload)
    preset_parser = subparsers.add_parser('preset', help='Upload with preset')
    preset_parser.add_argument('--account', required=True, help='Account username')
    preset_parser.add_argument('--region', choices=['us', 'gb', 'de'], required=True)
    
    args = parser.parse_args()
    
    # Presets
    PRESETS = {
        'us': {
            'video': VIDEOS_DIR / '3_39_m_sub.mp4',
            'caption': '🌙 Daily guidance ✨ What does the universe have for you today?\n\n#tarot #spirituality #dailyguidance #universe #energy'
        },
        'gb': {
            'video': VIDEOS_DIR / '3_39_m_en-GB_sub.mp4',
            'caption': '🌙 Your daily guidance ✨ What message awaits you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #uk'
        },
        'de': {
            'video': VIDEOS_DIR / '3_39_m_es-ES_sub.mp4',
            'caption': '🌙 ¿Qué te depara la luna hoy? ✨\n\n#calendariolunar #luna #astrologia #espiritualidad #tarot'
        }
    }
    
    if args.command == 'status':
        print("\n📊 ACCOUNT STATUS")
        print("="*50)
        for f in SESSIONS_DIR.glob("*_cookies.pkl"):
            username = f.stem.replace("_cookies", "")
            print(f"✅ {username}")
        return
    
    elif args.command == 'upload':
        uploader = SimpleReelUploader(args.account)
        success, msg = uploader.upload_reel(args.video, args.caption)
        
    elif args.command == 'preset':
        preset = PRESETS[args.region]
        uploader = SimpleReelUploader(args.account, args.region)
        success, msg = uploader.upload_reel(str(preset['video']), preset['caption'])
    
    else:
        print("\n📺 SIMPLE REEL UPLOADER")
        print("="*50)
        print("\nUsage:")
        print("  python simple_reel_uploader.py status")
        print("  python simple_reel_uploader.py preset --account USERNAME --region us|gb|de")
        print("  python simple_reel_uploader.py upload --account USERNAME --video PATH --caption 'TEXT'")
        print("\nAccounts with cookies:")
        for f in SESSIONS_DIR.glob("*_cookies.pkl"):
            username = f.stem.replace("_cookies", "")
            print(f"  - {username}")
        return
    
    print(f"\n{'='*50}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {msg}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
