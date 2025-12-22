#!/usr/bin/env python3
"""
VNC-based Reels Posting Script
Публикация Reels через VNC (visible browser, не headless)

Instagram блокирует headless браузеры, поэтому используем реальный браузер через VNC
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
from selenium.webdriver.common.action_chains import ActionChains

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


# Account configuration
ACCOUNTS = {
    'us': {
        'accounts': [
            'lourdesparsons20142',
            'michaelwagner19332', 
            'phillipjohnson1999',
        ],
        'video': '3_39_m_sub.mp4',
        'caption': '🌙 Daily guidance ✨ What does the universe have for you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing'
    },
    'gb': {
        'accounts': [
            'ceciliamotte19001',
            'douglasseedorff1944',
            'jameswhite19671'
        ],
        'video': '3_39_m_en-GB_sub.mp4',
        'caption': '🌙 Your daily guidance ✨ What message awaits you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing #uk'
    },
    'de': {
        'accounts': [
            'arthurlindsay20031',
            'janiethompson19151'
        ],
        'video': '3_39_m_es-ES_sub.mp4',
        'caption': '🌙 ¿Qué te depara la luna hoy? ✨\n\n#calendariolunar #luna #astrologia #espiritualidad #tarot #manifestacion'
    }
}


class VNCReelsPoster:
    """Reels poster using VNC display (visible browser)"""
    
    INSTAGRAM_BASE_URL = "https://www.instagram.com/"
    
    def __init__(self, username: str, country: str = 'us', use_profile: bool = True):
        self.username = username
        self.country = country
        self.use_profile = use_profile
        self.driver = None
        self.cookies = None
        
        # Chrome user data directory for profile persistence
        self.chrome_profile_dir = Path(f"/root/chrome_profiles/{username}")
        self.chrome_profile_dir.mkdir(parents=True, exist_ok=True)
    
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
        """Setup visible Chrome driver (VNC mode)"""
        options = Options()
        
        # NOT HEADLESS - visible browser
        # Set display to VNC
        os.environ['DISPLAY'] = ':1'
        
        # Use separate profile per account to preserve session
        if self.use_profile:
            options.add_argument(f"--user-data-dir={self.chrome_profile_dir}")
            logger.info(f"📁 Using profile: {self.chrome_profile_dir}")
        
        # Anti-detect
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        
        # Realistic user agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")
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
        
        # Maximize window
        driver.maximize_window()
        
        return driver
    
    def _apply_cookies(self) -> bool:
        """Apply cookies to driver"""
        if not self.cookies or not self.driver:
            return False
        
        try:
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(3)
            
            cookies_added = 0
            for cookie in self.cookies:
                try:
                    if 'sameSite' in cookie:
                        if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'Lax'
                    self.driver.add_cookie(cookie)
                    cookies_added += 1
                except Exception as e:
                    pass
            
            logger.info(f"✅ Applied {cookies_added} cookies")
            return True
        except Exception as e:
            logger.error(f"❌ Cookie error: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        try:
            time.sleep(3)
            
            # Check for login form (not logged in)
            try:
                login_form = self.driver.find_element(By.CSS_SELECTOR, "input[name='username']")
                if login_form.is_displayed():
                    return False
            except:
                pass
            
            # Check for create button or home elements (logged in)
            try:
                self.driver.find_element(By.XPATH, "//*[contains(@aria-label, 'New post') or contains(@aria-label, 'Create')]")
                return True
            except:
                pass
            
            # Check URL
            current_url = self.driver.current_url
            if 'accounts/login' in current_url:
                return False
            
            # Check page content
            page_source = self.driver.page_source.lower()
            if 'create' in page_source and 'search' in page_source:
                return True
            
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
            
            # Setup driver (visible mode)
            logger.info("🌐 Starting browser (VNC mode)...")
            self.driver = self._setup_driver()
            
            # Apply cookies
            if not self._apply_cookies():
                return False, "Failed to apply cookies"
            
            # Refresh and check
            self.driver.refresh()
            time.sleep(5)
            
            if not self._is_logged_in():
                logger.warning("⚠️ Cookies didn't work, trying with profile...")
                # Profile should have session
                self.driver.get(self.INSTAGRAM_BASE_URL)
                time.sleep(5)
                
                if not self._is_logged_in():
                    return False, "Not logged in - need to re-login via VNC manually"
            
            logger.info("✅ Successfully logged in")
            
            # Try to upload
            return self._do_upload(video_path, caption)
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False, str(e)
        finally:
            if self.driver:
                try:
                    # Screenshot
                    screenshot_path = LOGS_DIR / f"{self.username}_vnc_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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
            time.sleep(4)
            
            # Find Create button
            logger.info("🔍 Looking for Create button...")
            
            create_btn = None
            
            # Try multiple selectors
            selectors = [
                "//*[@aria-label='New post']",
                "//*[@aria-label='Create']",  
                "//svg[@aria-label='New post']/..",
                "//span[text()='Create']/..",
                "//*[contains(@class, '_ab6-')]//*[@aria-label='New post']",
                "//a[contains(@href, '/create/')]",
            ]
            
            for sel in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, sel)
                    for elem in elements:
                        if elem.is_displayed():
                            create_btn = elem
                            break
                    if create_btn:
                        break
                except:
                    continue
            
            # Try CSS as fallback
            if not create_btn:
                css_selectors = [
                    "[aria-label='New post']",
                    "[aria-label='Create']",
                    "a[href*='create']"
                ]
                for sel in css_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        for elem in elements:
                            if elem.is_displayed():
                                create_btn = elem
                                break
                        if create_btn:
                            break
                    except:
                        continue
            
            if not create_btn:
                # Last resort - try sidebar navigation
                try:
                    # Click on sidebar "Create" text
                    sidebar = self.driver.find_element(By.XPATH, "//nav//span[contains(text(), 'Create')]")
                    create_btn = sidebar.find_element(By.XPATH, "./..")
                except:
                    pass
            
            if not create_btn:
                return False, "Could not find Create button"
            
            logger.info("✅ Found Create button, clicking...")
            
            # Use ActionChains for more reliable click
            ActionChains(self.driver).move_to_element(create_btn).click().perform()
            time.sleep(4)
            
            # Look for Post type selection (Post vs Reel)
            try:
                # Sometimes Instagram shows a menu to choose post type
                reel_option = self.driver.find_element(By.XPATH, 
                    "//span[contains(text(), 'Reel') or contains(text(), 'reel')]"
                )
                reel_option.click()
                time.sleep(2)
            except:
                pass  # Continue if no type selection
            
            # Find file input
            logger.info("🔍 Looking for file input...")
            file_input = None
            
            try:
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except:
                # Click "Select from computer" if visible
                try:
                    select_btn = self.driver.find_element(By.XPATH, 
                        "//button[contains(text(), 'Select from computer') or contains(text(), 'Select')]"
                    )
                    select_btn.click()
                    time.sleep(2)
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                except:
                    pass
            
            if not file_input:
                return False, "Could not find file input"
            
            # Upload
            logger.info(f"📤 Uploading video: {video_path}")
            file_input.send_keys(video_path)
            
            # Wait for processing
            logger.info("⏳ Processing video (45 sec)...")
            time.sleep(45)
            
            # Click through Next buttons (usually 2-3 times)
            logger.info("⏭️ Navigating through wizard...")
            for i in range(4):
                try:
                    next_buttons = self.driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Next')]|//div[text()='Next']/ancestor::button|//div[text()='Next']/parent::div"
                    )
                    for btn in next_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            ActionChains(self.driver).move_to_element(btn).click().perform()
                            logger.info(f"   Clicked Next #{i+1}")
                            time.sleep(3)
                            break
                except Exception as e:
                    logger.debug(f"   Next button click {i}: {e}")
                    pass
            
            # Add caption
            logger.info("✏️ Adding caption...")
            try:
                # Try different caption selectors
                caption_selectors = [
                    "//textarea[@aria-label='Write a caption...']",
                    "//textarea[contains(@placeholder, 'caption')]",
                    "//div[@aria-label='Write a caption...']",
                    "//div[@role='textbox']"
                ]
                
                caption_input = None
                for sel in caption_selectors:
                    try:
                        caption_input = self.driver.find_element(By.XPATH, sel)
                        if caption_input.is_displayed():
                            break
                    except:
                        continue
                
                if caption_input:
                    ActionChains(self.driver).move_to_element(caption_input).click().perform()
                    time.sleep(0.5)
                    
                    # Type caption character by character (more reliable)
                    for char in caption:
                        caption_input.send_keys(char)
                        time.sleep(0.01)
                    
                    logger.info("✅ Caption added")
                else:
                    logger.warning("⚠️ Could not find caption input")
                    
            except Exception as e:
                logger.warning(f"⚠️ Caption error: {e}")
            
            time.sleep(3)
            
            # Click Share/Post
            logger.info("🚀 Sharing reel...")
            try:
                share_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Share')]|//div[text()='Share']/ancestor::button|//div[text()='Share']/parent::div"
                )
                for btn in share_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        ActionChains(self.driver).move_to_element(btn).click().perform()
                        logger.info("✅ Clicked Share")
                        break
            except:
                # Alternative: look for "Post" button
                try:
                    post_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Post')]")
                    post_btn.click()
                except:
                    pass
            
            # Wait for upload completion
            logger.info("⏳ Waiting for upload to complete (90 sec)...")
            time.sleep(90)
            
            # Check success indicators
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            if 'your reel has been shared' in page_source or 'shared' in page_source:
                return True, "🎉 Reel uploaded successfully!"
            
            if self.username in current_url or '/reels/' in current_url:
                return True, "🎉 Upload completed - check profile for reel"
            
            return True, "Upload initiated - verify on Instagram"
            
        except Exception as e:
            return False, str(e)


def run_vnc_posting(
    regions: List[str] = None,
    delay_between: int = 180,
    test_mode: bool = False
):
    """
    Run posting via VNC
    
    Args:
        regions: List of regions to post to (None = all)
        delay_between: Seconds between accounts
        test_mode: Only post to first account per region
    """
    logger.info("\n" + "="*70)
    logger.info("🖥️ VNC-BASED REELS POSTING")
    logger.info("="*70 + "\n")
    
    # Get logged in accounts
    logged_in = {'us': [], 'gb': [], 'de': []}
    for region, data in ACCOUNTS.items():
        for username in data['accounts']:
            cookie_file = SESSIONS_DIR / f"{username}_cookies.pkl"
            if cookie_file.exists():
                logged_in[region].append(username)
    
    total = sum(len(accs) for accs in logged_in.values())
    logger.info(f"📊 Found {total} logged-in accounts")
    
    results = {'success': [], 'failed': []}
    regions_to_process = regions or ['us', 'gb', 'de']
    
    for region in regions_to_process:
        if region not in ACCOUNTS:
            continue
        
        region_data = ACCOUNTS[region]
        video_file = region_data['video']
        caption = region_data['caption']
        accounts = logged_in.get(region, [])
        
        if not accounts:
            logger.warning(f"⚠️ No accounts for {region.upper()}")
            continue
        
        video_path = VIDEOS_DIR / video_file
        if not video_path.exists():
            logger.error(f"❌ Video not found: {video_path}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📍 REGION: {region.upper()}")
        logger.info(f"🎬 Video: {video_file}")
        logger.info(f"👥 Accounts: {accounts}")
        logger.info(f"{'='*60}")
        
        accounts_to_process = accounts[:1] if test_mode else accounts
        
        for i, username in enumerate(accounts_to_process):
            logger.info(f"\n[{i+1}/{len(accounts_to_process)}] Account: {username}")
            
            try:
                poster = VNCReelsPoster(
                    username=username,
                    country=region,
                    use_profile=True
                )
                
                success, message = poster.upload_reel(str(video_path), caption)
                
                if success:
                    logger.info(f"✅ SUCCESS: {username} - {message}")
                    results['success'].append({'username': username, 'region': region})
                else:
                    logger.error(f"❌ FAILED: {username} - {message}")
                    results['failed'].append({'username': username, 'region': region, 'error': message})
                    
            except Exception as e:
                logger.error(f"❌ ERROR: {username} - {e}")
                results['failed'].append({'username': username, 'region': region, 'error': str(e)})
            
            # Delay
            if i < len(accounts_to_process) - 1:
                delay = delay_between + random.randint(-30, 30)
                logger.info(f"⏳ Waiting {delay} seconds...")
                time.sleep(delay)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 SUMMARY")
    logger.info(f"✅ Success: {len(results['success'])}")
    logger.info(f"❌ Failed: {len(results['failed'])}")
    logger.info("="*70)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='VNC-based Reels Posting')
    parser.add_argument('--mode', choices=['status', 'post', 'test', 'single'], default='status')
    parser.add_argument('--regions', nargs='+', choices=['us', 'gb', 'de'])
    parser.add_argument('--account', type=str, help='Single account to post from')
    parser.add_argument('--delay', type=int, default=180)
    
    args = parser.parse_args()
    
    if args.mode == 'status':
        logger.info("\n📊 ACCOUNT STATUS")
        for region, data in ACCOUNTS.items():
            logger.info(f"\n{region.upper()}:")
            for acc in data['accounts']:
                cookie_file = SESSIONS_DIR / f"{acc}_cookies.pkl"
                status = "✅" if cookie_file.exists() else "❌"
                logger.info(f"   {status} {acc}")
    
    elif args.mode == 'single' and args.account:
        # Find account region
        region = None
        for r, data in ACCOUNTS.items():
            if args.account in data['accounts']:
                region = r
                break
        
        if not region:
            logger.error(f"Account {args.account} not found")
            return
        
        poster = VNCReelsPoster(args.account, region)
        video_path = VIDEOS_DIR / ACCOUNTS[region]['video']
        caption = ACCOUNTS[region]['caption']
        
        success, message = poster.upload_reel(str(video_path), caption)
        logger.info(f"Result: {message}")
    
    else:
        run_vnc_posting(
            regions=args.regions,
            delay_between=args.delay,
            test_mode=(args.mode == 'test')
        )


if __name__ == "__main__":
    main()
