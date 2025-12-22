"""
Email Parser Module
Handles email verification codes from firstmail.ltd and other providers
"""

import re
import time
import imaplib
import email
from email.header import decode_header
from typing import Optional, Tuple, List
import logging
from datetime import datetime, timedelta

# Selenium for web-based email
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailParser:
    """
    Email parser for retrieving Instagram verification codes
    Supports both IMAP and web-based email access
    """
    
    # Known IMAP servers
    IMAP_SERVERS = {
        'gmail.com': 'imap.gmail.com',
        'outlook.com': 'imap-mail.outlook.com',
        'hotmail.com': 'imap-mail.outlook.com',
        'yahoo.com': 'imap.mail.yahoo.com',
        'mail.ru': 'imap.mail.ru',
        'yandex.ru': 'imap.yandex.ru',
    }
    
    # Instagram verification code patterns
    CODE_PATTERNS = [
        r'verification code[:\s]+(\d{6})',
        r'security code[:\s]+(\d{6})',
        r'code[:\s]+(\d{6})',
        r'(\d{6})\s+is your Instagram',
        r'Instagram code[:\s]+(\d{6})',
        r'>(\d{6})<',  # HTML wrapped code
        r'\b(\d{6})\b',  # Fallback: any 6-digit number
    ]
    
    def __init__(self, email_address: str, email_password: str):
        self.email_address = email_address
        self.email_password = email_password
        self.domain = email_address.split('@')[-1].lower()
        
    def _get_imap_server(self) -> Optional[str]:
        """Get IMAP server for email domain"""
        return self.IMAP_SERVERS.get(self.domain)
    
    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract verification code from email text"""
        text = text.lower()
        
        for pattern in self.CODE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                logger.info(f"✅ Found code: {code}")
                return code
        
        return None
    
    def get_code_via_imap(self, timeout_seconds: int = 120) -> Optional[str]:
        """
        Get verification code via IMAP
        Waits for new email from Instagram
        """
        imap_server = self._get_imap_server()
        if not imap_server:
            logger.warning(f"⚠️ IMAP not supported for {self.domain}")
            return None
        
        logger.info(f"📧 Connecting to IMAP: {imap_server}")
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select('INBOX')
            
            start_time = time.time()
            
            while time.time() - start_time < timeout_seconds:
                # Search for recent emails from Instagram
                status, messages = mail.search(None, '(FROM "instagram" UNSEEN)')
                
                if status == 'OK' and messages[0]:
                    email_ids = messages[0].split()
                    
                    # Check latest emails first
                    for email_id in reversed(email_ids[-5:]):
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            raw_email = msg_data[0][1]
                            email_message = email.message_from_bytes(raw_email)
                            
                            # Get email body
                            body = ""
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        break
                                    elif part.get_content_type() == "text/html":
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            else:
                                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                            
                            # Extract code
                            code = self._extract_code_from_text(body)
                            if code:
                                mail.close()
                                mail.logout()
                                return code
                
                logger.info("⏳ Waiting for verification email...")
                time.sleep(5)
            
            mail.close()
            mail.logout()
            
            logger.warning("❌ Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logger.error(f"❌ IMAP error: {e}")
            return None
    
    def get_code_via_web(
        self, 
        webmail_url: str = "https://firstmail.ltd/ru-RU/webmail/login",
        timeout_seconds: int = 120,
        headless: bool = True
    ) -> Optional[str]:
        """
        Get verification code via web-based email client
        Specifically designed for firstmail.ltd
        """
        logger.info(f"🌐 Opening webmail: {webmail_url}")
        
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = None
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(webmail_url)
            time.sleep(3)
            
            # Login to webmail
            logger.info("🔐 Logging into webmail...")
            
            # Find and fill email field
            try:
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username'], input[id='email']"))
                )
                email_field.clear()
                email_field.send_keys(self.email_address)
            except TimeoutException:
                # Try alternative selectors
                email_field = driver.find_element(By.XPATH, "//input[@placeholder='Email' or @placeholder='Логин' or contains(@class, 'email')]")
                email_field.clear()
                email_field.send_keys(self.email_address)
            
            time.sleep(0.5)
            
            # Find and fill password field
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(self.email_password)
            except:
                password_field = driver.find_element(By.XPATH, "//input[@placeholder='Пароль' or @placeholder='Password']")
                password_field.clear()
                password_field.send_keys(self.email_password)
            
            time.sleep(0.5)
            
            # Click login button
            try:
                login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                login_btn.click()
            except:
                login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Войти') or contains(text(), 'Login') or contains(text(), 'Sign')]")
                login_btn.click()
            
            logger.info("⏳ Waiting for inbox to load...")
            time.sleep(5)
            
            start_time = time.time()
            
            while time.time() - start_time < timeout_seconds:
                # Refresh inbox
                try:
                    driver.refresh()
                    time.sleep(3)
                except:
                    pass
                
                # Look for Instagram emails
                page_source = driver.page_source
                
                # Check for Instagram in email list
                if 'instagram' in page_source.lower():
                    logger.info("📨 Found Instagram email!")
                    
                    # Try to click on Instagram email
                    try:
                        instagram_email = driver.find_element(By.XPATH, "//*[contains(text(), 'Instagram') or contains(text(), 'instagram')]")
                        instagram_email.click()
                        time.sleep(2)
                    except:
                        pass
                    
                    # Get updated page source (email content)
                    page_source = driver.page_source
                    
                    # Extract code
                    code = self._extract_code_from_text(page_source)
                    if code:
                        return code
                
                logger.info("⏳ Waiting for verification email...")
                time.sleep(10)
            
            logger.warning("❌ Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logger.error(f"❌ Webmail error: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def get_verification_code(self, timeout_seconds: int = 120) -> Optional[str]:
        """
        Get Instagram verification code
        Tries IMAP first, falls back to web
        """
        # Check if IMAP is available
        if self._get_imap_server():
            code = self.get_code_via_imap(timeout_seconds)
            if code:
                return code
        
        # Fall back to web-based email
        # For firstmail.ltd and other web-only providers
        if 'firstmail' in self.domain or not self._get_imap_server():
            return self.get_code_via_web(timeout_seconds=timeout_seconds)
        
        return None


class FirstMailParser(EmailParser):
    """
    Specialized parser for firstmail.ltd and similar email services
    Handles both web-based and API access
    """
    
    WEBMAIL_URL = "https://firstmail.ltd/ru-RU/webmail/login"
    API_URL = "https://firstmail.ltd/api"
    
    def __init__(self, email_address: str, email_password: str):
        super().__init__(email_address, email_password)
        
    def get_code_via_api(self, timeout_seconds: int = 180) -> Optional[str]:
        """
        Try to get verification code via API (if available)
        Falls back to web scraping if API not available
        """
        import requests
        
        try:
            # Try API endpoints
            session = requests.Session()
            
            # Login attempt
            login_data = {
                'email': self.email_address,
                'password': self.email_password
            }
            
            # This is a placeholder - actual API endpoint may differ
            # Most temp email services don't have public APIs
            logger.info("API not available for firstmail.ltd, using web scraping")
            return None
            
        except Exception as e:
            logger.debug(f"API attempt failed: {e}")
            return None
    
    def get_code_via_web_enhanced(self, timeout_seconds: int = 180) -> Optional[str]:
        """
        Enhanced web scraping for firstmail.ltd
        More robust selectors and error handling
        """
        logger.info(f"\U0001F310 Opening firstmail.ltd for: {self.email_address}")
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = None
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            
            # Navigate to login page
            driver.get(self.WEBMAIL_URL)
            time.sleep(3)
            
            logger.info("\U0001F510 Logging into firstmail.ltd...")
            
            # Multiple selector strategies for login form
            email_selectors = [
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='email']"),
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.CSS_SELECTOR, "input[id='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='mail']"),
                (By.CSS_SELECTOR, "input[placeholder*='\u041b\u043e\u0433\u0438\u043d']"),
                (By.XPATH, "//input[@type='text' or @type='email'][1]")
            ]
            
            email_field = None
            for selector_type, selector in email_selectors:
                try:
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if email_field.is_displayed():
                        break
                except:
                    continue
            
            if not email_field:
                logger.error("\u274C Could not find email field")
                return None
            
            # Clear and enter email
            email_field.clear()
            email_field.send_keys(self.email_address)
            time.sleep(0.5)
            
            # Find password field
            password_selectors = [
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            password_field = None
            for selector_type, selector in password_selectors:
                try:
                    password_field = driver.find_element(selector_type, selector)
                    if password_field.is_displayed():
                        break
                except:
                    continue
            
            if not password_field:
                logger.error("\u274C Could not find password field")
                return None
            
            password_field.clear()
            password_field.send_keys(self.email_password)
            time.sleep(0.5)
            
            # Find and click login button
            login_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), '\u0412\u043e\u0439\u0442\u0438')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign')]"),
                (By.CSS_SELECTOR, ".login-btn, .submit-btn, .btn-primary")
            ]
            
            login_btn = None
            for selector_type, selector in login_selectors:
                try:
                    login_btn = driver.find_element(selector_type, selector)
                    if login_btn.is_displayed():
                        break
                except:
                    continue
            
            if login_btn:
                login_btn.click()
            else:
                # Try pressing Enter
                password_field.send_keys(Keys.RETURN)
            
            logger.info("\u23F3 Waiting for inbox to load...")
            time.sleep(5)
            
            start_time = time.time()
            check_count = 0
            
            while time.time() - start_time < timeout_seconds:
                check_count += 1
                logger.info(f"\u23F3 Checking for Instagram email... (attempt {check_count})")
                
                # Refresh to get new emails
                try:
                    driver.refresh()
                    time.sleep(4)
                except:
                    pass
                
                page_source = driver.page_source
                
                # Check for Instagram email
                if 'instagram' in page_source.lower():
                    logger.info("\U0001F4E8 Found Instagram email!")
                    
                    # Try to click on Instagram email row
                    instagram_selectors = [
                        (By.XPATH, "//*[contains(translate(text(), 'INSTAGRAM', 'instagram'), 'instagram')]"),
                        (By.XPATH, "//tr[contains(., 'Instagram') or contains(., 'instagram')]"),
                        (By.XPATH, "//div[contains(., 'Instagram') or contains(., 'instagram')]//ancestor::tr"),
                        (By.CSS_SELECTOR, "tr.email-row, .message-row, .mail-item")
                    ]
                    
                    for selector_type, selector in instagram_selectors:
                        try:
                            email_row = driver.find_element(selector_type, selector)
                            if email_row.is_displayed():
                                email_row.click()
                                time.sleep(2)
                                break
                        except:
                            continue
                    
                    # Get page source after clicking
                    page_source = driver.page_source
                    
                    # Extract verification code
                    code = self._extract_code_from_text(page_source)
                    if code:
                        logger.info(f"\u2705 Found verification code: {code}")
                        return code
                
                # Wait before next check
                time.sleep(10)
            
            logger.warning("\u274C Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logger.error(f"\u274C Webmail error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def get_verification_code(self, timeout_seconds: int = 180) -> Optional[str]:
        """
        Get code from firstmail.ltd
        Tries API first, then enhanced web scraping
        """
        # Try API first (usually not available)
        code = self.get_code_via_api(timeout_seconds)
        if code:
            return code
        
        # Fall back to enhanced web scraping
        return self.get_code_via_web_enhanced(timeout_seconds)


def get_email_parser(email_address: str, email_password: str) -> EmailParser:
    """
    Factory function to get appropriate email parser
    """
    domain = email_address.split('@')[-1].lower()
    
    # Known domains mapping
    if 'firstmail' in domain:
        return FirstMailParser(email_address, email_password)
    
    # Generic domains with custom handling
    custom_domains = {
        'hydrofertty.com': FirstMailParser,
        'cryobioltty.com': FirstMailParser,
        'eudiometty.com': FirstMailParser,
        'neocolotty.com': FirstMailParser,
        'duodenojejtty.com': FirstMailParser,
        'leukoctty.com': FirstMailParser,
        'pathophtty.com': FirstMailParser,
        'sociobitty.com': FirstMailParser,
        'maintaitty.com': FirstMailParser,
        'megalosytty.com': FirstMailParser,
    }
    
    parser_class = custom_domains.get(domain, EmailParser)
    return parser_class(email_address, email_password)


# ============== Test ==============

if __name__ == "__main__":
    # Test email parser
    test_email = "lourdesparsons2014@hydrofertty.com"
    test_password = "caewtnwgA!6261"
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing Email Parser")
    print(f"{'='*60}")
    print(f"Email: {test_email}")
    
    parser = get_email_parser(test_email, test_password)
    print(f"Parser type: {type(parser).__name__}")
    
    # Note: Actual test would require triggering a verification email
    print("\n⚠️ To test, trigger an Instagram verification email first")
    print("Then run: parser.get_verification_code()")
