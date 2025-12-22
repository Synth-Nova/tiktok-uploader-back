"""
Instagram Auto Login Module
Автоматический логин в Instagram с обработкой email верификации
"""

import os
import sys
import time
import json
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

# Selenium with Wire for proxy support
try:
    from seleniumwire import webdriver as wire_webdriver
    SELENIUM_WIRE_AVAILABLE = True
except ImportError:
    SELENIUM_WIRE_AVAILABLE = False

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modules.email_parser import get_email_parser, FirstMailParser
from src.utils.fingerprint_generator import generate_fingerprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramAutoLogin:
    """
    Автоматический логин в Instagram с поддержкой:
    - Прокси (Decodo)
    - Anti-detect fingerprints
    - Email верификация (firstmail.ltd)
    - Сохранение cookies/сессий
    """
    
    INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"
    INSTAGRAM_BASE_URL = "https://www.instagram.com/"
    
    # Data directory for cookies
    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
    
    def __init__(
        self,
        username: str,
        password: str,
        email: str,
        email_password: str,
        proxy: Optional[Dict[str, Any]] = None,
        country: str = "us",
        headless: bool = True
    ):
        self.username = username
        self.password = password
        self.email = email
        self.email_password = email_password
        self.proxy = proxy
        self.country = country
        self.headless = headless
        
        self.driver = None
        self.cookies = None
        self.session_id = None
        
        # Create data directory
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize fingerprint
        self.fingerprint = generate_fingerprint(country)
        
        # Initialize email parser
        self.email_parser = get_email_parser(email, email_password)
        
    def _get_cookies_path(self) -> Path:
        """Get path for cookies file"""
        return self.DATA_DIR / f"{self.username}_cookies.pkl"
    
    def _get_session_path(self) -> Path:
        """Get path for session data"""
        return self.DATA_DIR / f"{self.username}_session.json"
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with anti-detect options"""
        options = Options()
        
        # Headless mode
        if self.headless:
            options.add_argument("--headless=new")
        
        # Anti-detect options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        
        # Window size from fingerprint
        screen_width = self.fingerprint.get('screenWidth', 1920)
        screen_height = self.fingerprint.get('screenHeight', 1080)
        options.add_argument(f"--window-size={screen_width},{screen_height}")
        
        # User-Agent from fingerprint
        user_agent = self.fingerprint.get('userAgent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument(f"--user-agent={user_agent}")
        
        # Language from fingerprint
        lang = self.fingerprint.get('language', 'en-US')
        options.add_argument(f"--lang={lang}")
        
        options.add_argument("--disable-gpu")
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Setup proxy with selenium-wire if available
        # NOTE: Can be disabled by setting proxy=None
        seleniumwire_options = None
        use_proxy = self.proxy and SELENIUM_WIRE_AVAILABLE and self.proxy.get('enabled', True)
        if use_proxy:
            proxy_url = f"http://{self.proxy['user']}:{self.proxy['password']}@{self.proxy['host']}:{self.proxy['port']}"
            seleniumwire_options = {
                'proxy': {
                    'http': proxy_url,
                    'https': proxy_url,
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            logger.info(f"\U0001F510 Using selenium-wire proxy: {self.proxy['host']}:{self.proxy['port']}")
        elif self.proxy:
            # Fallback to simple proxy (no auth)
            proxy_string = f"{self.proxy['host']}:{self.proxy['port']}"
            options.add_argument(f"--proxy-server=http://{proxy_string}")
            logger.info(f"\U0001F310 Using simple proxy (no auth): {proxy_string}")
        
        # Create driver
        if seleniumwire_options and use_proxy:
            driver = wire_webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        else:
            if not use_proxy:
                logger.info("⚠️ Proxy disabled, connecting directly")
            driver = webdriver.Chrome(options=options)
        
        # Execute CDP commands for anti-detect
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                // Webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            '''
        })
        
        # Set timezone from fingerprint
        timezone = self.fingerprint.get('timezone', 'America/New_York')
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': timezone
        })
        
        return driver
    
    def _load_cookies(self) -> bool:
        """Load saved cookies if available"""
        cookies_path = self._get_cookies_path()
        
        if cookies_path.exists():
            try:
                with open(cookies_path, 'rb') as f:
                    self.cookies = pickle.load(f)
                logger.info(f"✅ Loaded cookies for {self.username}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Failed to load cookies: {e}")
        
        return False
    
    def _save_cookies(self) -> bool:
        """Save cookies to file"""
        if not self.driver:
            return False
        
        try:
            cookies = self.driver.get_cookies()
            cookies_path = self._get_cookies_path()
            
            with open(cookies_path, 'wb') as f:
                pickle.dump(cookies, f)
            
            # Also save session info
            session_data = {
                'username': self.username,
                'country': self.country,
                'saved_at': datetime.now().isoformat(),
                'cookies_count': len(cookies)
            }
            
            with open(self._get_session_path(), 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"✅ Saved {len(cookies)} cookies for {self.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save cookies: {e}")
            return False
    
    def _apply_cookies(self) -> bool:
        """Apply saved cookies to driver"""
        if not self.cookies or not self.driver:
            return False
        
        try:
            # First navigate to Instagram domain
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(2)
            
            # Add each cookie
            for cookie in self.cookies:
                try:
                    # Remove problematic fields
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
        """Check if currently logged into Instagram"""
        try:
            self.driver.get(self.INSTAGRAM_BASE_URL)
            time.sleep(3)
            
            # Check for login indicators
            page_source = self.driver.page_source.lower()
            
            # If we see profile elements, we're logged in
            if 'create' in page_source or '/direct/inbox' in page_source:
                # Double check by looking for avatar or profile link
                try:
                    self.driver.find_element(By.XPATH, "//span[contains(@class, 'x1lliihq')]")
                    return True
                except:
                    pass
                
                try:
                    self.driver.find_element(By.XPATH, f"//a[contains(@href, '/{self.username}')]")
                    return True
                except:
                    pass
            
            # Check if login form is present (not logged in)
            if 'log in' in page_source or 'phone number, username' in page_source:
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking login status: {e}")
            return False
    
    def _handle_verification_code(self) -> bool:
        """
        Handle email verification code request
        """
        logger.info("🔐 Email verification required!")
        logger.info(f"📧 Checking email: {self.email}")
        
        try:
            # Wait for verification code from email
            # Start polling email in parallel with waiting
            code = None
            
            # Get code from email parser
            logger.info("⏳ Waiting for verification code in email...")
            code = self.email_parser.get_verification_code(timeout_seconds=180)
            
            if not code:
                logger.error("❌ Failed to get verification code from email")
                return False
            
            logger.info(f"✅ Got verification code: {code}")
            
            # Find verification input field
            try:
                code_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        "input[name='verificationCode'], input[name='security_code'], input[type='text']"
                    ))
                )
            except:
                # Alternative selectors
                code_input = self.driver.find_element(By.XPATH, 
                    "//input[@name='verificationCode' or @name='security_code' or @aria-label='Security Code']"
                )
            
            # Clear and enter code
            code_input.clear()
            time.sleep(0.3)
            
            # Type code character by character
            for digit in code:
                code_input.send_keys(digit)
                time.sleep(0.1)
            
            time.sleep(1)
            
            # Find and click confirm button
            try:
                confirm_btn = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Confirm') or contains(text(), 'Submit') or contains(text(), 'Подтвердить')]"
                )
                confirm_btn.click()
            except:
                # Try pressing Enter
                code_input.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            # Check if verification was successful
            if self._is_logged_in():
                logger.info("✅ Verification successful!")
                return True
            
            # Check for error messages
            page_source = self.driver.page_source.lower()
            if 'incorrect' in page_source or 'try again' in page_source:
                logger.error("❌ Verification code was incorrect")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling verification: {e}")
            return False
    
    def _handle_suspicious_activity(self) -> bool:
        """Handle suspicious login activity challenge"""
        logger.warning("⚠️ Suspicious activity detected!")
        
        try:
            page_source = self.driver.page_source.lower()
            
            # Check for email verification option
            if 'send security code' in page_source or 'email' in page_source:
                # Click "Send code" or similar button
                try:
                    send_code_btn = self.driver.find_element(By.XPATH,
                        "//button[contains(text(), 'Send') or contains(text(), 'Email') or contains(text(), 'Отправить')]"
                    )
                    send_code_btn.click()
                    time.sleep(3)
                    
                    # Now handle verification code
                    return self._handle_verification_code()
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error handling suspicious activity: {e}")
            return False
    
    def login(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Perform login to Instagram
        
        Returns:
            Tuple of (success: bool, message: str, cookies: dict or None)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Starting login for: {self.username}")
        logger.info(f"🌍 Country: {self.country.upper()}")
        if self.proxy:
            logger.info(f"🔌 Proxy: {self.proxy['host']}:{self.proxy['port']}")
        logger.info(f"{'='*60}")
        
        try:
            # Initialize driver
            logger.info("🌐 Starting browser...")
            self.driver = self._setup_driver()
            
            # Try to use saved cookies first
            if self._load_cookies():
                logger.info("🍪 Trying saved cookies...")
                if self._apply_cookies():
                    # Refresh and check if logged in
                    self.driver.refresh()
                    time.sleep(3)
                    
                    if self._is_logged_in():
                        logger.info("✅ Logged in via saved cookies!")
                        return True, "Logged in via cookies", self.cookies
            
            # Fresh login required
            logger.info("🔐 Performing fresh login...")
            
            # Navigate to login page
            self.driver.get(self.INSTAGRAM_LOGIN_URL)
            time.sleep(3)
            
            # Handle cookie consent if present
            try:
                cookie_btn = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Принять')]"
                )
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Find username field
            try:
                username_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
            except TimeoutException:
                return False, "Login page failed to load", None
            
            # Enter username
            username_input.clear()
            time.sleep(0.3)
            for char in self.username:
                username_input.send_keys(char)
                time.sleep(0.05)
            
            time.sleep(0.5)
            
            # Find password field
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            time.sleep(0.3)
            for char in self.password:
                password_input.send_keys(char)
                time.sleep(0.05)
            
            time.sleep(0.5)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            logger.info("⏳ Waiting for response...")
            time.sleep(5)
            
            # Check result
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            # Check for various scenarios
            
            # 1. Verification code required
            if 'security code' in page_source or 'verification code' in page_source or 'confirm it' in page_source:
                if self._handle_verification_code():
                    self._save_cookies()
                    return True, "Logged in with email verification", self.driver.get_cookies()
                else:
                    return False, "Email verification failed", None
            
            # 2. Suspicious activity
            if 'suspicious' in page_source or 'unusual' in page_source or 'we detected' in page_source:
                if self._handle_suspicious_activity():
                    self._save_cookies()
                    return True, "Logged in after suspicious activity check", self.driver.get_cookies()
                else:
                    return False, "Suspicious activity block", None
            
            # 3. Wrong password
            if 'incorrect' in page_source or 'password was incorrect' in page_source:
                return False, "Wrong password", None
            
            # 4. Account disabled
            if 'disabled' in page_source or 'suspended' in page_source:
                return False, "Account disabled/suspended", None
            
            # 5. Challenge required
            if 'challenge' in current_url:
                return False, "Challenge required (manual intervention needed)", None
            
            # 6. Check if successfully logged in
            if self._is_logged_in():
                logger.info("✅ Login successful!")
                self._save_cookies()
                return True, "Login successful", self.driver.get_cookies()
            
            # 7. Save not now (notifications popup)
            try:
                not_now_btn = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Not Now') or contains(text(), 'Не сейчас')]"
                )
                not_now_btn.click()
                time.sleep(2)
                
                if self._is_logged_in():
                    self._save_cookies()
                    return True, "Login successful", self.driver.get_cookies()
            except:
                pass
            
            return False, "Unknown login result", None
            
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False, f"Error: {str(e)}", None
            
        finally:
            if self.driver:
                # Take screenshot for debugging
                try:
                    screenshot_path = self.DATA_DIR / f"{self.username}_last.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                except:
                    pass
                
                # Close driver
                self.driver.quit()
                logger.info("🔒 Browser closed")
    
    def logout(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


def auto_login_account(account: Dict[str, Any], save_cookies: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """
    Helper function to login a single account
    
    Args:
        account: Dict with username, password, email, email_password, country, proxy
        save_cookies: Whether to save cookies on success
        
    Returns:
        Tuple of (success, message, cookies)
    """
    login = InstagramAutoLogin(
        username=account['username'],
        password=account['password'],
        email=account['email'],
        email_password=account['email_password'],
        proxy=account.get('proxy'),
        country=account.get('country', 'us'),
        headless=True
    )
    
    return login.login()


# ============== Test ==============

if __name__ == "__main__":
    # Test with first account
    test_account = {
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
    }
    
    print(f"\n{'='*60}")
    print("🧪 Testing Instagram Auto Login")
    print(f"{'='*60}")
    
    success, message, cookies = auto_login_account(test_account)
    
    print(f"\n{'='*60}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {message}")
    print(f"Cookies: {len(cookies) if cookies else 0} items")
    print(f"{'='*60}")
