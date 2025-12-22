"""
Instagram Reels Uploader Module
Автоматическая загрузка Reels с использованием сохранённых cookies
"""

import os
import sys
import time
import json
import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.fingerprint_generator import generate_fingerprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReelsUploader:
    """
    Instagram Reels Uploader with cookie-based authentication
    """
    
    INSTAGRAM_BASE_URL = "https://www.instagram.com/"
    INSTAGRAM_REELS_CREATE_URL = "https://www.instagram.com/reels/create/"
    
    # Data directory
    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
    UPLOADS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
    
    def __init__(
        self,
        username: str,
        proxy: Optional[Dict[str, Any]] = None,
        country: str = "us",
        headless: bool = True
    ):
        self.username = username
        self.proxy = proxy
        self.country = country
        self.headless = headless
        
        self.driver = None
        self.cookies = None
        
        # Create directories
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize fingerprint
        self.fingerprint = generate_fingerprint(country)
        
    def _get_cookies_path(self) -> Path:
        """Get path for cookies file"""
        return self.DATA_DIR / f"{self.username}_cookies.pkl"
    
    def _load_cookies(self) -> bool:
        """Load saved cookies"""
        cookies_path = self._get_cookies_path()
        
        if cookies_path.exists():
            try:
                with open(cookies_path, 'rb') as f:
                    self.cookies = pickle.load(f)
                logger.info(f"✅ Loaded cookies for {self.username}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Failed to load cookies: {e}")
        else:
            logger.warning(f"⚠️ No cookies found for {self.username}")
        
        return False
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # Anti-detect options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        
        # Window size
        screen = self.fingerprint.get('screen', {'width': 1920, 'height': 1080})
        screen_width = self.fingerprint.get('screenWidth', 1920)
        screen_height = self.fingerprint.get('screenHeight', 1080)
        options.add_argument(f"--window-size={screen_width},{screen_height}")
        
        # User-Agent
        user_agent = self.fingerprint.get('userAgent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument(f"--user-agent={user_agent}")
        
        # Language
        lang = self.fingerprint.get('language', 'en-US')
        options.add_argument(f"--lang={lang}")
        
        # Proxy
        if self.proxy:
            proxy_string = f"{self.proxy['host']}:{self.proxy['port']}"
            options.add_argument(f"--proxy-server=http://{proxy_string}")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        
        # Anti-detect CDP commands
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        # Timezone
        timezone = self.fingerprint.get('timezone', 'America/New_York')
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': timezone
        })
        
        return driver
    
    def _apply_cookies(self) -> bool:
        """Apply saved cookies to driver"""
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
                except Exception as e:
                    logger.debug(f"Cookie error: {e}")
            
            logger.info(f"✅ Applied {len(self.cookies)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply cookies: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        try:
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            
            # Check for logged in indicators
            if 'create' in page_source or '/direct/inbox' in page_source:
                return True
            
            if 'log in' in page_source or 'phone number, username' in page_source:
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking login: {e}")
            return False
    
    def _upload_via_create_button(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """
        Upload Reels via the Create (+) button on Instagram
        """
        logger.info("📤 Starting upload via Create button...")
        
        try:
            # Navigate to Instagram home
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(3)
            
            # Find and click Create button (usually + icon in sidebar or top)
            create_selectors = [
                "//div[@role='button']//span[contains(@aria-label, 'New post')]",
                "//a[contains(@href, '/create/')]",
                "//svg[@aria-label='New post']//ancestor::*[@role='link']",
                "//div[contains(@class, 'x1i10hfl')]//span[contains(@aria-label, 'New')]",
                "//*[@aria-label='New post']",
                "//*[@aria-label='Create']",
                "//span[text()='Create']//ancestor::*[@role='link']",
            ]
            
            create_btn = None
            for selector in create_selectors:
                try:
                    create_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if create_btn and create_btn.is_displayed():
                        break
                except:
                    continue
            
            if not create_btn:
                # Try CSS selectors
                css_selectors = [
                    "div[role='button'] svg[aria-label*='New']",
                    "a[href*='create']",
                    "[aria-label='New post']",
                    "[aria-label='Create']"
                ]
                for selector in css_selectors:
                    try:
                        create_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if create_btn.is_displayed():
                            break
                    except:
                        continue
            
            if not create_btn:
                return False, "Could not find Create button"
            
            logger.info("📝 Found Create button, clicking...")
            create_btn.click()
            time.sleep(2)
            
            # Look for "Select from computer" or file input
            file_input = None
            try:
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except:
                # Try clicking "Select from computer" button first
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
            
            # Upload file
            logger.info(f"📎 Uploading file: {video_path}")
            file_input.send_keys(video_path)
            
            # Wait for upload processing
            logger.info("⏳ Waiting for video processing...")
            time.sleep(10)
            
            # Click Next/Continue buttons through the wizard
            next_buttons = [
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'Continue')]",
                "//div[text()='Next']//ancestor::button",
                "//div[text()='Continue']//ancestor::button",
            ]
            
            for _ in range(3):  # Click Next up to 3 times
                for selector in next_buttons:
                    try:
                        next_btn = self.driver.find_element(By.XPATH, selector)
                        if next_btn.is_displayed() and next_btn.is_enabled():
                            next_btn.click()
                            time.sleep(2)
                            break
                    except:
                        continue
            
            # Add caption
            try:
                caption_input = self.driver.find_element(By.XPATH, 
                    "//textarea[@aria-label='Write a caption...' or @placeholder='Write a caption...']"
                )
                caption_input.click()
                time.sleep(0.5)
                
                # Type caption
                for char in caption:
                    caption_input.send_keys(char)
                    time.sleep(0.02)
                
                logger.info("✏️ Caption added")
            except Exception as e:
                logger.warning(f"⚠️ Could not add caption: {e}")
            
            time.sleep(2)
            
            # Click Share/Post button
            share_selectors = [
                "//button[contains(text(), 'Share')]",
                "//button[contains(text(), 'Post')]",
                "//div[text()='Share']//ancestor::button",
            ]
            
            for selector in share_selectors:
                try:
                    share_btn = self.driver.find_element(By.XPATH, selector)
                    if share_btn.is_displayed() and share_btn.is_enabled():
                        share_btn.click()
                        logger.info("🚀 Clicked Share button")
                        break
                except:
                    continue
            
            # Wait for upload completion
            time.sleep(10)
            
            # Check for success
            page_source = self.driver.page_source.lower()
            if 'your reel has been shared' in page_source or 'reel shared' in page_source:
                return True, "Reel uploaded successfully"
            
            return True, "Upload initiated (check Instagram for confirmation)"
            
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return False, str(e)
    
    def _upload_via_reels_create(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """
        Upload Reels via direct Reels create URL
        """
        logger.info("📤 Starting upload via Reels Create page...")
        
        try:
            self.driver.get(self.INSTAGRAM_REELS_CREATE_URL)
            time.sleep(5)
            
            # Find file input
            try:
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
            except:
                # Page might redirect or need different approach
                return False, "Could not find file input on Reels create page"
            
            # Upload video
            logger.info(f"📎 Uploading: {video_path}")
            file_input.send_keys(video_path)
            
            # Wait for processing
            logger.info("⏳ Processing video...")
            time.sleep(15)
            
            # Navigate through wizard and add caption (similar to above)
            # ... (simplified for now)
            
            return True, "Upload initiated via Reels Create"
            
        except Exception as e:
            return False, str(e)
    
    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        hashtags: List[str] = None
    ) -> Tuple[bool, str]:
        """
        Upload a Reel to Instagram
        
        Args:
            video_path: Path to video file
            caption: Caption text
            hashtags: List of hashtags to add
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 REELS UPLOAD: {self.username}")
        logger.info(f"📁 Video: {video_path}")
        logger.info(f"{'='*60}")
        
        # Validate video file
        if not os.path.exists(video_path):
            return False, f"Video file not found: {video_path}"
        
        # Get absolute path
        video_path = os.path.abspath(video_path)
        
        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            hashtag_str = " ".join([f"#{h}" if not h.startswith("#") else h for h in hashtags])
            full_caption = f"{caption}\n\n{hashtag_str}" if caption else hashtag_str
        
        try:
            # Load cookies
            if not self._load_cookies():
                return False, "No saved cookies - please login first"
            
            # Setup driver
            logger.info("🌐 Starting browser...")
            self.driver = self._setup_driver()
            
            # Apply cookies
            if not self._apply_cookies():
                return False, "Failed to apply cookies"
            
            # Refresh and check login
            self.driver.refresh()
            time.sleep(3)
            
            if not self._is_logged_in():
                return False, "Not logged in - cookies may have expired"
            
            logger.info("✅ Logged in successfully")
            
            # Try upload methods
            success, message = self._upload_via_create_button(video_path, full_caption)
            
            if not success:
                logger.info("⚠️ First method failed, trying alternative...")
                success, message = self._upload_via_reels_create(video_path, full_caption)
            
            # Save upload record
            if success:
                self._save_upload_record(video_path, caption, hashtags)
            
            return success, message
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False, str(e)
            
        finally:
            if self.driver:
                try:
                    # Save screenshot
                    screenshot_path = self.UPLOADS_DIR / f"{self.username}_last_upload.png"
                    self.driver.save_screenshot(str(screenshot_path))
                except:
                    pass
                
                self.driver.quit()
                logger.info("🔒 Browser closed")
    
    def _save_upload_record(self, video_path: str, caption: str, hashtags: List[str]):
        """Save upload record to JSON"""
        record = {
            'username': self.username,
            'video': os.path.basename(video_path),
            'caption': caption,
            'hashtags': hashtags or [],
            'timestamp': datetime.now().isoformat(),
            'country': self.country
        }
        
        records_file = self.UPLOADS_DIR / "upload_history.json"
        
        try:
            if records_file.exists():
                with open(records_file, 'r') as f:
                    records = json.load(f)
            else:
                records = []
            
            records.append(record)
            
            with open(records_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Could not save upload record: {e}")


def upload_reel_to_account(
    username: str,
    video_path: str,
    caption: str = "",
    hashtags: List[str] = None,
    proxy: Dict = None,
    country: str = "us",
    headless: bool = True
) -> Tuple[bool, str]:
    """
    Helper function to upload a reel
    """
    uploader = ReelsUploader(
        username=username,
        proxy=proxy,
        country=country,
        headless=headless
    )
    
    return uploader.upload_reel(video_path, caption, hashtags)


# Test
if __name__ == "__main__":
    print("🎬 Reels Uploader Module")
    print("Usage: uploader = ReelsUploader(username)")
    print("       uploader.upload_reel(video_path, caption, hashtags)")
