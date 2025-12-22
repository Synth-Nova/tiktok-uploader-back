"""
GoLogin API Integration Module
Creates and manages browser profiles with anti-detect fingerprints
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoLoginAPI:
    """
    GoLogin API Client for managing browser profiles
    """
    
    BASE_URL = "https://api.gologin.com"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            if response.status_code in [200, 201]:
                return response.json() if response.text else {}
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
    
    def get_profiles(self) -> List[dict]:
        """Get all browser profiles"""
        result = self._request("GET", "/browser/v2")
        if "profiles" in result:
            return result["profiles"]
        return result if isinstance(result, list) else []
    
    def get_profile(self, profile_id: str) -> dict:
        """Get single profile by ID"""
        return self._request("GET", f"/browser/{profile_id}")
    
    def create_profile(self, profile_config: dict) -> dict:
        """Create new browser profile"""
        return self._request("POST", "/browser", profile_config)
    
    def update_profile(self, profile_id: str, profile_config: dict) -> dict:
        """Update existing profile"""
        return self._request("PUT", f"/browser/{profile_id}", profile_config)
    
    def delete_profile(self, profile_id: str) -> dict:
        """Delete profile"""
        return self._request("DELETE", f"/browser/{profile_id}")
    
    def start_profile(self, profile_id: str) -> dict:
        """Start browser profile (get WebSocket URL for connection)"""
        return self._request("GET", f"/browser/{profile_id}/start")
    
    def stop_profile(self, profile_id: str) -> dict:
        """Stop browser profile"""
        return self._request("GET", f"/browser/{profile_id}/stop")


class GoLoginProfileManager:
    """
    Manages GoLogin profiles for Instagram accounts
    """
    
    # Country-specific configurations
    COUNTRY_CONFIGS = {
        'us': {
            'name': 'United States',
            'os': 'win',
            'language': 'en-US,en',
            'timezone': 'America/New_York',
            'webrtc_mode': 'altered',
            'geo': {
                'latitude': 40.7128,
                'longitude': -74.0060,
                'accuracy': 100
            }
        },
        'gb': {
            'name': 'United Kingdom',
            'os': 'win',
            'language': 'en-GB,en',
            'timezone': 'Europe/London',
            'webrtc_mode': 'altered',
            'geo': {
                'latitude': 51.5074,
                'longitude': -0.1278,
                'accuracy': 100
            }
        },
        'de': {
            'name': 'Germany',
            'os': 'win',
            'language': 'de-DE,de,en',
            'timezone': 'Europe/Berlin',
            'webrtc_mode': 'altered',
            'geo': {
                'latitude': 52.5200,
                'longitude': 13.4050,
                'accuracy': 100
            }
        },
    }
    
    def __init__(self, api_token: str):
        self.api = GoLoginAPI(api_token)
        self.profiles = {}
    
    def create_instagram_profile(
        self,
        name: str,
        country_code: str,
        proxy: dict,
        notes: str = ""
    ) -> Optional[dict]:
        """
        Create a GoLogin profile optimized for Instagram
        """
        config = self.COUNTRY_CONFIGS.get(country_code.lower(), self.COUNTRY_CONFIGS['us'])
        
        # Profile configuration
        profile_config = {
            "name": name,
            "notes": notes,
            "browserType": "chrome",
            "os": config['os'],
            "navigator": {
                "language": config['language'],
                "userAgent": "random",  # GoLogin will generate
                "resolution": "1920x1080",
                "platform": "Win32"
            },
            "proxy": {
                "mode": "http",
                "host": proxy['host'],
                "port": proxy['port'],
                "username": proxy['user'],
                "password": proxy['password']
            },
            "timezone": {
                "enabled": True,
                "fillBasedOnIp": False,
                "timezone": config['timezone']
            },
            "geolocation": {
                "mode": "prompt",
                "enabled": True,
                "customize": True,
                "fillBasedOnIp": False,
                "latitude": config['geo']['latitude'],
                "longitude": config['geo']['longitude'],
                "accuracy": config['geo']['accuracy']
            },
            "webRTC": {
                "mode": "alerted",
                "enabled": True,
                "customize": True,
                "fillBasedOnIp": True
            },
            "canvas": {
                "mode": "noise"
            },
            "webGL": {
                "mode": "noise"
            },
            "webGLMetadata": {
                "mode": "mask"
            },
            "audioContext": {
                "mode": "noise"
            },
            "fonts": {
                "enableMasking": True,
                "enableDomRect": True,
                "families": ["Arial", "Verdana", "Times New Roman", "Georgia", "Courier New"]
            },
            "mediaDevices": {
                "enableMasking": True,
                "videoInputs": 1,
                "audioInputs": 1,
                "audioOutputs": 1
            },
            "storage": {
                "local": True,
                "extensions": True,
                "bookmarks": True,
                "history": True,
                "passwords": True,
                "session": True
            }
        }
        
        logger.info(f"Creating profile: {name} ({country_code.upper()})")
        result = self.api.create_profile(profile_config)
        
        if "id" in result:
            logger.info(f"✅ Profile created: {result['id']}")
            return result
        else:
            logger.error(f"❌ Failed to create profile: {result}")
            return None
    
    def create_profiles_for_accounts(self, accounts: List[dict]) -> List[dict]:
        """
        Create GoLogin profiles for multiple Instagram accounts
        """
        created_profiles = []
        
        for account in accounts:
            profile_name = f"IG_{account['username']}"
            
            proxy = {
                'host': account['proxy_host'],
                'port': account['proxy_port'],
                'user': account['proxy_user'],
                'password': account['proxy_pass']
            }
            
            profile = self.create_instagram_profile(
                name=profile_name,
                country_code=account['country_code'],
                proxy=proxy,
                notes=f"Instagram: {account['username']}"
            )
            
            if profile:
                created_profiles.append({
                    'account_id': account['id'],
                    'username': account['username'],
                    'profile_id': profile['id'],
                    'country': account['country_code']
                })
            
            # Delay between profile creation
            time.sleep(1)
        
        return created_profiles
    
    def get_all_profiles(self) -> List[dict]:
        """Get all profiles from GoLogin"""
        return self.api.get_profiles()
    
    def delete_all_profiles(self) -> int:
        """Delete all profiles (use with caution!)"""
        profiles = self.get_all_profiles()
        deleted = 0
        
        for profile in profiles:
            result = self.api.delete_profile(profile['id'])
            if 'error' not in result:
                deleted += 1
                logger.info(f"Deleted profile: {profile['name']}")
            time.sleep(0.5)
        
        return deleted


# ============== Test Functions ==============

def test_api_connection(api_token: str) -> bool:
    """Test GoLogin API connection"""
    print("\n" + "=" * 60)
    print("🔍 Testing GoLogin API Connection")
    print("=" * 60)
    
    api = GoLoginAPI(api_token)
    profiles = api.get_profiles()
    
    if isinstance(profiles, dict) and 'error' in profiles:
        print(f"❌ Connection failed: {profiles['error']}")
        return False
    
    print(f"✅ Connection successful!")
    print(f"📊 Found {len(profiles)} existing profiles")
    
    return True


def create_test_profiles(api_token: str):
    """Create profiles for all 10 Instagram accounts"""
    
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.database import get_all_accounts
    
    print("\n" + "=" * 60)
    print("🚀 Creating GoLogin Profiles for Instagram Accounts")
    print("=" * 60)
    
    # Get accounts from database
    accounts = get_all_accounts()
    print(f"📋 Found {len(accounts)} accounts in database")
    
    # Create profile manager
    manager = GoLoginProfileManager(api_token)
    
    # Create profiles
    created = manager.create_profiles_for_accounts(accounts)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"✅ Created: {len(created)}/{len(accounts)} profiles")
    
    if created:
        print("\n📋 Created Profiles:")
        for p in created:
            print(f"   • {p['username']} ({p['country'].upper()}) → {p['profile_id']}")
    
    return created


if __name__ == "__main__":
    # GoLogin API Token
    API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTM1YTRiZjM5NmM0ZDhmMmYxOWU4ZDYiLCJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2OTM1YTU1ZjAwYjNhMGMwMDM3OTNlNzUifQ._VjG7vTTDtjUxeNIqEagiiRTU_x_BrlSRhcFhmrUtnw"
    
    # Test connection
    if test_api_connection(API_TOKEN):
        # Create profiles
        create_test_profiles(API_TOKEN)
