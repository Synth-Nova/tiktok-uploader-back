"""
GoLogin Browser Controller
Launches browser profiles and controls them via Selenium
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoLoginBrowser:
    """
    Controls GoLogin browser profiles via API and Selenium
    """
    
    API_URL = "https://api.gologin.com"
    
    def __init__(self, api_token: str, profile_id: str):
        self.api_token = api_token
        self.profile_id = profile_id
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.driver = None
        self.ws_url = None
    
    def start_profile(self) -> Optional[str]:
        """
        Start GoLogin profile and get WebSocket debugger URL
        Returns WebSocket URL for Selenium connection
        """
        logger.info(f"🚀 Starting GoLogin profile: {self.profile_id}")
        
        try:
            # Start profile via API
            response = requests.get(
                f"{self.API_URL}/browser/{self.profile_id}/start",
                headers=self.headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                self.ws_url = data.get('wsUrl') or data.get('ws', {}).get('puppeteer')
                
                if self.ws_url:
                    logger.info(f"✅ Profile started! WebSocket: {self.ws_url[:50]}...")
                    return self.ws_url
                else:
                    logger.error(f"❌ No WebSocket URL in response: {data}")
                    return None
            else:
                logger.error(f"❌ Failed to start profile: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error starting profile: {e}")
            return None
    
    def stop_profile(self):
        """Stop GoLogin profile"""
        try:
            response = requests.get(
                f"{self.API_URL}/browser/{self.profile_id}/stop",
                headers=self.headers,
                timeout=30
            )
            logger.info(f"Profile stopped: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error stopping profile: {e}")
    
    def connect_selenium(self) -> bool:
        """
        Connect Selenium to running GoLogin browser
        """
        if not self.ws_url:
            logger.error("No WebSocket URL. Start profile first!")
            return False
        
        try:
            # Extract debugger address from WebSocket URL
            # ws://127.0.0.1:XXXXX/devtools/browser/...
            # We need: 127.0.0.1:XXXXX
            
            debugger_address = self.ws_url.replace("ws://", "").split("/devtools")[0]
            
            options = Options()
            options.add_experimental_option("debuggerAddress", debugger_address)
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("✅ Selenium connected to GoLogin browser!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect Selenium: {e}")
            return False
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get Selenium WebDriver"""
        return self.driver
    
    def close(self):
        """Close browser and stop profile"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.stop_profile()


class InstagramLoginWithGoLogin:
    """
    Instagram login using GoLogin anti-detect browser
    """
    
    def __init__(self, gologin_browser: GoLoginBrowser):
        self.browser = gologin_browser
        self.driver = None
    
    def _random_sleep(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random delay to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _human_type(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _random_mouse_movement(self):
        """Random mouse movements"""
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 4)):
                actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
                actions.pause(random.uniform(0.1, 0.2))
            actions.perform()
        except:
            pass
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Perform Instagram login
        Returns: (success, message)
        """
        self.driver = self.browser.get_driver()
        
        if not self.driver:
            return False, "No browser driver"
        
        try:
            logger.info(f"🔐 Logging into Instagram as {username}...")
            
            # Navigate to Instagram login
            self.driver.get("https://www.instagram.com/accounts/login/")
            self._random_sleep(3, 5)
            
            # Handle cookie consent
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Разрешить')]"))
                )
                cookie_btn.click()
                self._random_sleep(1, 2)
            except TimeoutException:
                pass
            
            # Random mouse movement
            self._random_mouse_movement()
            
            # Find and fill username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
            )
            username_field.click()
            self._random_sleep(0.3, 0.7)
            self._human_type(username_field, username)
            self._random_sleep(0.5, 1)
            
            # Find and fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            password_field.click()
            self._random_sleep(0.3, 0.7)
            self._human_type(password_field, password)
            self._random_sleep(0.5, 1)
            
            # Random mouse movement
            self._random_mouse_movement()
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            logger.info("⏳ Waiting for login response...")
            self._random_sleep(5, 8)
            
            # Check result
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check for various states
            if "challenge" in current_url or "two_factor" in current_url:
                logger.warning("🔐 2FA/Challenge required")
                return False, "2FA_REQUIRED"
            
            if "suspicious" in page_source or "unusual" in page_source:
                logger.warning("⚠️ Suspicious login detected")
                return False, "SUSPICIOUS_LOGIN"
            
            if "incorrect" in page_source or "wrong" in page_source:
                logger.error("❌ Wrong password")
                return False, "WRONG_PASSWORD"
            
            if "disabled" in page_source or "suspended" in page_source:
                logger.error("🚫 Account disabled")
                return False, "ACCOUNT_DISABLED"
            
            # Check for successful login
            if "instagram.com" in current_url and "login" not in current_url:
                # Handle popups
                self._handle_post_login_popups()
                
                logger.info(f"✅ Successfully logged in as {username}!")
                return True, "SUCCESS"
            
            return False, "UNKNOWN_ERROR"
            
        except TimeoutException:
            return False, "TIMEOUT"
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False, str(e)
    
    def _handle_post_login_popups(self):
        """Handle post-login popups (Save login, notifications)"""
        # "Save Login Info" popup
        try:
            not_now = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Not now') or contains(text(), 'Не сейчас')]"))
            )
            not_now.click()
            self._random_sleep(1, 2)
        except:
            pass
        
        # Notifications popup
        try:
            not_now = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Not now') or contains(text(), 'Не сейчас')]"))
            )
            not_now.click()
            self._random_sleep(1, 2)
        except:
            pass
    
    def get_cookies(self) -> list:
        """Get browser cookies after login"""
        if self.driver:
            return self.driver.get_cookies()
        return []


# ============== Account-Profile Mapping ==============

ACCOUNT_PROFILES = {
    "charleshenry19141": {
        "profile_id": "6935a5c6a5909ce6f04e2adc",
        "password": "vujlkedeY!6778",
        "country": "de"
    },
    "arthurlindsay20031": {
        "profile_id": "6935a5c8a5909ce6f04e2cdc",
        "password": "ogycwedgY!7232",
        "country": "de"
    },
    "janiethompson19151": {
        "profile_id": "6935a5c96476c900c7a813d9",
        "password": "czuxpdanS!2107",
        "country": "de"
    },
    "ceciliamotte19001": {
        "profile_id": "6935a5ca6821728274ca24ab",
        "password": "mepwfkhiX!4210",
        "country": "gb"
    },
    "douglasseedorff1944": {
        "profile_id": "6935a5cb6821728274ca258c",
        "password": "dinfpdwaY!3078",
        "country": "gb"
    }
}


def test_login(username: str):
    """Test login for a specific account"""
    
    API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTM1YTRiZjM5NmM0ZDhmMmYxOWU4ZDYiLCJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2OTM1YTU1ZjAwYjNhMGMwMDM3OTNlNzUifQ._VjG7vTTDtjUxeNIqEagiiRTU_x_BrlSRhcFhmrUtnw"
    
    if username not in ACCOUNT_PROFILES:
        print(f"❌ Account {username} not found!")
        return
    
    account = ACCOUNT_PROFILES[username]
    
    print("\n" + "=" * 60)
    print(f"🧪 Testing Instagram Login via GoLogin")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Country: {account['country'].upper()}")
    print(f"Profile ID: {account['profile_id']}")
    print("=" * 60)
    
    # Create GoLogin browser
    browser = GoLoginBrowser(API_TOKEN, account['profile_id'])
    
    try:
        # Start profile
        ws_url = browser.start_profile()
        if not ws_url:
            print("❌ Failed to start GoLogin profile")
            return
        
        # Wait for browser to fully start
        print("⏳ Waiting for browser to initialize...")
        time.sleep(5)
        
        # Connect Selenium
        if not browser.connect_selenium():
            print("❌ Failed to connect Selenium")
            return
        
        # Perform login
        ig_login = InstagramLoginWithGoLogin(browser)
        success, message = ig_login.login(username, account['password'])
        
        print("\n" + "=" * 60)
        if success:
            print("✅ LOGIN SUCCESSFUL!")
            cookies = ig_login.get_cookies()
            print(f"🍪 Cookies: {len(cookies)} items")
        else:
            print(f"❌ LOGIN FAILED: {message}")
        print("=" * 60)
        
        # Keep browser open for inspection
        input("\n⏎ Press Enter to close browser...")
        
    finally:
        browser.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_login(sys.argv[1])
    else:
        print("Available accounts:")
        for username in ACCOUNT_PROFILES:
            print(f"  • {username}")
        print("\nUsage: python gologin_browser.py <username>")
