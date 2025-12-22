"""
Instagram Authentication Module
Handles login with anti-detect measures and email verification
"""

import os
import sys
import time
import json
import random
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.fingerprint_generator import generate_fingerprint, get_fingerprint_injection_script, get_chrome_args_from_fingerprint

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InstagramAuth:
    """
    Instagram authentication handler with anti-detect capabilities
    """
    
    INSTAGRAM_URL = "https://www.instagram.com/"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    
    def __init__(
        self,
        username: str,
        password: str,
        proxy: Optional[Dict] = None,
        fingerprint: Optional[Dict] = None,
        chrome_profile_path: Optional[str] = None,
        headless: bool = False
    ):
        self.username = username
        self.password = password
        self.proxy = proxy
        self.fingerprint = fingerprint or generate_fingerprint('us')
        self.chrome_profile_path = chrome_profile_path
        self.headless = headless
        self.driver = None
        self.cookies = []
        
    def _get_chrome_options(self) -> Options:
        """Configure Chrome options with anti-detect measures"""
        options = Options()
        
        # Anti-detect arguments
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        
        # Window size from fingerprint
        width = self.fingerprint.get('screenWidth', 1920)
        height = self.fingerprint.get('screenHeight', 1080)
        options.add_argument(f"--window-size={width},{height}")
        
        # Language from fingerprint
        lang = self.fingerprint.get('language', 'en-US')
        options.add_argument(f"--lang={lang}")
        
        # User Agent
        user_agent = self.fingerprint.get('userAgent')
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")
        
        # Timezone
        timezone = self.fingerprint.get('timezone', 'America/New_York')
        options.add_argument(f"--timezone={timezone}")
        
        # Chrome profile (for session persistence)
        if self.chrome_profile_path:
            options.add_argument(f"--user-data-dir={self.chrome_profile_path}")
        
        # Proxy configuration
        if self.proxy:
            proxy_str = self._format_proxy_string()
            if proxy_str:
                options.add_argument(f"--proxy-server={proxy_str}")
        
        # Headless mode
        if self.headless:
            options.add_argument("--headless=new")
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "intl.accept_languages": lang,
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _format_proxy_string(self) -> Optional[str]:
        """Format proxy for Chrome"""
        if not self.proxy:
            return None
        
        host = self.proxy.get('host')
        port = self.proxy.get('port')
        
        if host and port:
            return f"http://{host}:{port}"
        return None
    
    def _get_proxy_extension(self) -> Optional[str]:
        """
        Create Chrome extension for proxy authentication
        Required when proxy needs username/password
        """
        if not self.proxy or not self.proxy.get('user'):
            return None
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        
        background_js = """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
            }
        };
        
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        
        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """ % (
            self.proxy['host'],
            self.proxy['port'],
            self.proxy['user'],
            self.proxy['password']
        )
        
        # Create extension directory
        import tempfile
        import zipfile
        
        ext_dir = tempfile.mkdtemp()
        ext_path = os.path.join(ext_dir, 'proxy_auth.zip')
        
        with zipfile.ZipFile(ext_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        return ext_path
    
    def _inject_fingerprint(self):
        """Inject fingerprint spoofing JavaScript"""
        try:
            js_code = get_fingerprint_injection_script(self.fingerprint)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': js_code
            })
            logger.info("✅ Fingerprint injection applied")
        except Exception as e:
            logger.warning(f"⚠️ Could not inject fingerprint: {e}")
    
    def _apply_stealth_measures(self):
        """Apply additional stealth measures via CDP"""
        try:
            # Hide webdriver
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            
            # Override plugins
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                '''
            })
            
            # Override permissions
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                '''
            })
            
            logger.info("✅ Stealth measures applied")
        except Exception as e:
            logger.warning(f"⚠️ Could not apply stealth measures: {e}")
    
    def start_browser(self) -> bool:
        """Start Chrome browser with anti-detect configuration"""
        try:
            options = self._get_chrome_options()
            
            # Add proxy auth extension if needed
            proxy_ext = self._get_proxy_extension()
            if proxy_ext:
                options.add_extension(proxy_ext)
            
            # Start Chrome
            self.driver = webdriver.Chrome(options=options)
            
            # Apply stealth measures
            self._apply_stealth_measures()
            self._inject_fingerprint()
            
            # Set timezone via CDP
            timezone = self.fingerprint.get('timezone', 'America/New_York')
            self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                'timezoneId': timezone
            })
            
            logger.info(f"✅ Browser started for {self.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser: {e}")
            return False
    
    def _human_type(self, element, text: str, delay_range: Tuple[float, float] = (0.05, 0.15)):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*delay_range))
    
    def _random_sleep(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random sleep to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _random_mouse_movement(self):
        """Perform random mouse movements"""
        try:
            actions = ActionChains(self.driver)
            
            # Random movements
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.1, 0.3))
            
            actions.perform()
        except:
            pass
    
    def login(self) -> Tuple[bool, str]:
        """
        Perform Instagram login
        Returns: (success: bool, message: str)
        """
        if not self.driver:
            if not self.start_browser():
                return False, "Failed to start browser"
        
        try:
            logger.info(f"🔐 Logging in as {self.username}...")
            
            # Navigate to login page
            self.driver.get(self.LOGIN_URL)
            self._random_sleep(3, 5)
            
            # Handle cookie consent if present
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]"))
                )
                cookie_btn.click()
                self._random_sleep(1, 2)
            except TimeoutException:
                pass
            
            # Random mouse movement
            self._random_mouse_movement()
            
            # Find username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
            )
            
            # Click and type username
            username_field.click()
            self._random_sleep(0.5, 1)
            self._human_type(username_field, self.username)
            self._random_sleep(0.5, 1.5)
            
            # Find password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            password_field.click()
            self._random_sleep(0.3, 0.7)
            self._human_type(password_field, self.password)
            self._random_sleep(0.5, 1.5)
            
            # Random mouse movement before clicking login
            self._random_mouse_movement()
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            logger.info("⏳ Waiting for login response...")
            self._random_sleep(5, 8)
            
            # Check for various outcomes
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check for 2FA / verification
            if "challenge" in current_url or "two_factor" in current_url:
                logger.warning("🔐 Two-factor authentication required")
                return False, "2FA_REQUIRED"
            
            # Check for email verification
            if "confirm_email" in current_url or "verify" in page_source:
                logger.warning("📧 Email verification required")
                return False, "EMAIL_VERIFICATION_REQUIRED"
            
            # Check for suspicious login
            if "suspicious" in page_source or "unusual" in page_source:
                logger.warning("⚠️ Suspicious login detected")
                return False, "SUSPICIOUS_LOGIN"
            
            # Check for wrong password
            if "incorrect" in page_source or "wrong" in page_source:
                logger.error("❌ Wrong password")
                return False, "WRONG_PASSWORD"
            
            # Check for account disabled
            if "disabled" in page_source or "suspended" in page_source:
                logger.error("🚫 Account is disabled/suspended")
                return False, "ACCOUNT_DISABLED"
            
            # Check for successful login (redirected to home or feed)
            if "instagram.com" in current_url and "login" not in current_url:
                # Handle "Save Login Info" popup
                try:
                    not_now_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Not now')]"))
                    )
                    not_now_btn.click()
                    self._random_sleep(1, 2)
                except TimeoutException:
                    pass
                
                # Handle notifications popup
                try:
                    not_now_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Not now')]"))
                    )
                    not_now_btn.click()
                    self._random_sleep(1, 2)
                except TimeoutException:
                    pass
                
                # Save cookies
                self.cookies = self.driver.get_cookies()
                logger.info(f"✅ Successfully logged in as {self.username}")
                
                return True, "SUCCESS"
            
            # Unknown state
            logger.warning(f"⚠️ Unknown login state. URL: {current_url}")
            return False, "UNKNOWN_ERROR"
            
        except TimeoutException as e:
            logger.error(f"❌ Timeout during login: {e}")
            return False, "TIMEOUT"
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False, str(e)
    
    def get_cookies(self) -> List[Dict]:
        """Get saved cookies"""
        return self.cookies
    
    def load_cookies(self, cookies: List[Dict]) -> bool:
        """Load cookies into browser"""
        try:
            if not self.driver:
                self.start_browser()
            
            # First navigate to Instagram
            self.driver.get(self.INSTAGRAM_URL)
            self._random_sleep(2, 3)
            
            # Add cookies
            for cookie in cookies:
                try:
                    # Remove problematic fields
                    cookie_clean = {k: v for k, v in cookie.items() 
                                   if k not in ['sameSite', 'expiry', 'httpOnly', 'secure']}
                    self.driver.add_cookie(cookie_clean)
                except Exception as e:
                    logger.debug(f"Cookie error: {e}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            self._random_sleep(3, 5)
            
            # Check if logged in
            if "login" not in self.driver.current_url:
                logger.info("✅ Session restored from cookies")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to load cookies: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """Check if currently logged in"""
        try:
            if not self.driver:
                return False
            
            self.driver.get(self.INSTAGRAM_URL)
            self._random_sleep(3, 5)
            
            # Check URL
            if "login" in self.driver.current_url:
                return False
            
            # Check for profile icon or home feed elements
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
                )
                return True
            except TimeoutException:
                pass
            
            return False
            
        except Exception:
            return False
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# ============== Test Function ==============

def test_login(username: str, password: str, proxy: Dict = None, country: str = 'us'):
    """Test Instagram login"""
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing Instagram Login")
    print(f"{'='*60}")
    print(f"Username: {username}")
    print(f"Country: {country}")
    print(f"Proxy: {proxy['host'] if proxy else 'None'}")
    
    # Generate fingerprint
    fingerprint = generate_fingerprint(country)
    print(f"Fingerprint: {fingerprint['userAgent'][:50]}...")
    
    # Create auth instance
    auth = InstagramAuth(
        username=username,
        password=password,
        proxy=proxy,
        fingerprint=fingerprint,
        headless=False  # Set to True for production
    )
    
    try:
        # Attempt login
        success, message = auth.login()
        
        print(f"\n{'='*60}")
        if success:
            print(f"✅ LOGIN SUCCESS!")
            print(f"Cookies saved: {len(auth.get_cookies())} cookies")
        else:
            print(f"❌ LOGIN FAILED: {message}")
        print(f"{'='*60}")
        
        return success, message, auth.get_cookies()
        
    finally:
        # Keep browser open for debugging
        input("\nPress Enter to close browser...")
        auth.close()


if __name__ == "__main__":
    # Test with first account
    test_account = {
        "username": "lourdesparsons20142",
        "password": "caewtnwgA!6261",
        "email": "lourdesparsons2014@hydrofertty.com",
        "email_password": "caewtnwgA!6261"
    }
    
    test_proxy = {
        "host": "us.decodo.com",
        "port": 10001,
        "user": "spvzzn2tmc",
        "password": "gbLZ8rl9y=VlXx37je"
    }
    
    test_login(
        username=test_account["username"],
        password=test_account["password"],
        proxy=test_proxy,
        country='us'
    )
