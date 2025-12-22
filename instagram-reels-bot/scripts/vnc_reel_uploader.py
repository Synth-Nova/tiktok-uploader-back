#!/usr/bin/env python3
"""
VNC Reel Uploader - Uses existing Chrome session
Использует уже залогиненную сессию Chrome из VNC
"""

import os
import sys
import time
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
VIDEOS_DIR = BASE_DIR / "data" / "videos"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Chrome profile path (where VNC logins are saved)
CHROME_PROFILE = Path("/root/.config/google-chrome")


class VNCReelUploader:
    """Upload Reels using existing VNC Chrome session"""
    
    INSTAGRAM_BASE_URL = "https://www.instagram.com/"
    
    def __init__(self):
        self.driver = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver using existing profile"""
        # Set VNC display
        os.environ['DISPLAY'] = ':1'
        
        options = Options()
        
        # Use existing Chrome profile (contains all logged-in sessions)
        options.add_argument(f"--user-data-dir={CHROME_PROFILE}")
        options.add_argument("--profile-directory=Default")
        
        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        logger.info("🌐 Starting Chrome with existing profile...")
        driver = webdriver.Chrome(options=options)
        
        # Anti-detect
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        driver.maximize_window()
        return driver
    
    def is_logged_in(self) -> bool:
        """Check if currently logged into Instagram"""
        try:
            time.sleep(2)
            
            # Check for login form
            try:
                login_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='username']")
                if login_input.is_displayed():
                    return False
            except:
                pass
            
            # Check URL
            if 'accounts/login' in self.driver.current_url:
                return False
            
            # Check for logged-in elements
            page_source = self.driver.page_source.lower()
            if 'create' in page_source or 'home' in page_source:
                return True
            
            return True  # Assume logged in if no login form
            
        except Exception as e:
            logger.error(f"Login check error: {e}")
            return False
    
    def get_current_account(self) -> str:
        """Try to get current logged-in account name"""
        try:
            # Look for profile link
            profile_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '/') and contains(@role, 'link')]//img")
            href = profile_link.find_element(By.XPATH, "..").get_attribute("href")
            if href:
                username = href.strip('/').split('/')[-1]
                if username and username not in ['', 'accounts', 'direct', 'explore']:
                    return username
        except:
            pass
        return "unknown"
    
    def upload_reel(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """
        Upload a Reel to Instagram
        
        Args:
            video_path: Path to video file
            caption: Caption text with hashtags
            
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(video_path):
            return False, f"Video not found: {video_path}"
        
        video_path = os.path.abspath(video_path)
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎬 UPLOADING REEL")
            logger.info(f"📁 Video: {video_path}")
            logger.info(f"{'='*60}")
            
            # Setup driver
            self.driver = self._setup_driver()
            
            # Go to Instagram
            logger.info("📱 Opening Instagram...")
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(5)
            
            # Check if logged in
            if not self.is_logged_in():
                return False, "Not logged in - please login via VNC first"
            
            account = self.get_current_account()
            logger.info(f"✅ Logged in as: {account}")
            
            # Start upload process
            return self._do_upload(video_path, caption)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False, str(e)
        finally:
            if self.driver:
                try:
                    screenshot_path = LOGS_DIR / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                except:
                    pass
                
                # Don't quit - leave browser open
                # self.driver.quit()
                logger.info("ℹ️ Browser left open for verification")
    
    def _do_upload(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """Perform the upload"""
        try:
            # Step 1: Find and click Create button
            logger.info("🔍 Step 1: Finding Create button...")
            
            create_btn = None
            selectors = [
                "//*[@aria-label='New post']",
                "//*[@aria-label='Create']",
                "//span[text()='Create']/ancestor::*[@role='link' or @role='button']",
                "//svg[@aria-label='New post']/ancestor::*[self::a or self::div[@role='button']]",
            ]
            
            # Wait for page to fully load
            time.sleep(3)
            
            for sel in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, sel)
                    for elem in elements:
                        if elem.is_displayed():
                            create_btn = elem
                            logger.info(f"   Found via: {sel[:50]}...")
                            break
                    if create_btn:
                        break
                except:
                    continue
            
            if not create_btn:
                # Try CSS
                for sel in ["[aria-label='New post']", "[aria-label='Create']"]:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if elem.is_displayed():
                            create_btn = elem
                            break
                    except:
                        continue
            
            if not create_btn:
                # Take screenshot for debugging
                self.driver.save_screenshot(str(LOGS_DIR / "no_create_button.png"))
                return False, "Could not find Create button"
            
            # Click create
            logger.info("   Clicking Create...")
            ActionChains(self.driver).move_to_element(create_btn).click().perform()
            time.sleep(3)
            
            # Step 2: Find file input and upload
            logger.info("🔍 Step 2: Finding file input...")
            
            file_input = None
            try:
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except:
                # Click "Select from computer" button if visible
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
            
            # Upload video
            logger.info(f"   Uploading: {os.path.basename(video_path)}")
            file_input.send_keys(video_path)
            
            # Step 3: Wait for processing
            logger.info("⏳ Step 3: Processing video (60 sec)...")
            time.sleep(60)
            
            # Step 4: Click Next buttons (usually 2-3 times)
            logger.info("⏭️ Step 4: Navigating wizard...")
            
            for i in range(4):
                try:
                    next_btn = self.driver.find_element(By.XPATH,
                        "//button[.//text()='Next' or text()='Next']|"
                        "//div[text()='Next']/ancestor::button|"
                        "//div[text()='Next']/parent::div[@role='button']"
                    )
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        ActionChains(self.driver).move_to_element(next_btn).click().perform()
                        logger.info(f"   Clicked Next #{i+1}")
                        time.sleep(3)
                except:
                    pass
            
            # Step 5: Add caption
            logger.info("✏️ Step 5: Adding caption...")
            
            try:
                caption_selectors = [
                    "//textarea[@aria-label='Write a caption...']",
                    "//div[@aria-label='Write a caption...']",
                    "//div[@role='textbox' and @contenteditable='true']",
                    "//textarea[contains(@placeholder, 'caption')]"
                ]
                
                caption_input = None
                for sel in caption_selectors:
                    try:
                        elem = self.driver.find_element(By.XPATH, sel)
                        if elem.is_displayed():
                            caption_input = elem
                            break
                    except:
                        continue
                
                if caption_input:
                    ActionChains(self.driver).move_to_element(caption_input).click().perform()
                    time.sleep(0.5)
                    
                    # Type caption
                    for char in caption:
                        caption_input.send_keys(char)
                        time.sleep(0.01)
                    
                    logger.info("   ✅ Caption added")
                else:
                    logger.warning("   ⚠️ Caption input not found")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Caption error: {e}")
            
            time.sleep(2)
            
            # Step 6: Click Share
            logger.info("🚀 Step 6: Sharing...")
            
            try:
                share_btn = self.driver.find_element(By.XPATH,
                    "//button[.//text()='Share' or text()='Share']|"
                    "//div[text()='Share']/ancestor::button|"
                    "//div[text()='Share']/parent::div[@role='button']"
                )
                if share_btn.is_displayed():
                    ActionChains(self.driver).move_to_element(share_btn).click().perform()
                    logger.info("   ✅ Clicked Share")
            except:
                try:
                    post_btn = self.driver.find_element(By.XPATH, "//button[text()='Post']")
                    post_btn.click()
                except:
                    logger.warning("   ⚠️ Could not find Share/Post button")
            
            # Step 7: Wait for completion
            logger.info("⏳ Step 7: Waiting for upload (120 sec)...")
            time.sleep(120)
            
            # Check result
            page_source = self.driver.page_source.lower()
            
            if 'your reel has been shared' in page_source or 'reel shared' in page_source:
                return True, "🎉 Reel uploaded successfully!"
            
            return True, "Upload completed - verify on Instagram"
            
        except Exception as e:
            return False, str(e)


def main():
    parser = argparse.ArgumentParser(description='VNC Reel Uploader')
    parser.add_argument('--video', type=str, help='Video file path')
    parser.add_argument('--caption', type=str, default='', help='Caption text')
    parser.add_argument('--region', choices=['us', 'gb', 'de'], help='Use preset for region')
    
    args = parser.parse_args()
    
    # Presets
    PRESETS = {
        'us': {
            'video': VIDEOS_DIR / '3_39_m_sub.mp4',
            'caption': '🌙 Daily guidance ✨ What does the universe have for you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing'
        },
        'gb': {
            'video': VIDEOS_DIR / '3_39_m_en-GB_sub.mp4',
            'caption': '🌙 Your daily guidance ✨ What message awaits you today?\n\n#tarot #spirituality #dailyguidance #universe #energy #manifestation #healing #uk'
        },
        'de': {
            'video': VIDEOS_DIR / '3_39_m_es-ES_sub.mp4',
            'caption': '🌙 ¿Qué te depara la luna hoy? ✨\n\n#calendariolunar #luna #astrologia #espiritualidad #tarot #manifestacion'
        }
    }
    
    if args.region:
        preset = PRESETS[args.region]
        video_path = str(preset['video'])
        caption = preset['caption']
    elif args.video:
        video_path = args.video
        caption = args.caption
    else:
        # Show usage
        print("\n📺 VNC REEL UPLOADER")
        print("="*50)
        print("\nUsage:")
        print("  python vnc_reel_uploader.py --region us")
        print("  python vnc_reel_uploader.py --video /path/to/video.mp4 --caption 'My caption'")
        print("\nPresets:")
        for region, data in PRESETS.items():
            print(f"  {region.upper()}: {data['video'].name}")
        print("\n⚠️ Requirements:")
        print("  1. VNC server running on :1")
        print("  2. Already logged into Instagram via Chrome")
        print("  3. No other Chrome instance using the profile")
        return
    
    # Check video exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    # Run uploader
    uploader = VNCReelUploader()
    success, message = uploader.upload_reel(video_path, caption)
    
    print(f"\n{'='*50}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {message}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
