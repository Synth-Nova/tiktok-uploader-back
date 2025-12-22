#!/usr/bin/env python3
"""
DuoPlus Cloud Phone API Integration
Documentation: https://help.duoplus.net/docs/api-reference

ВАЖНО: Для работы API необходимо:
1. Войти в панель DuoPlus: https://my.duoplus.net/
2. Перейти в Settings / API Configuration
3. Включить API доступ
4. Скопировать API Key

API Base URL: https://api.duoplus.net/api/v1
Authorization: Bearer <API_KEY>
"""

import requests
import json
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class PhoneStatus(Enum):
    STOPPED = 0
    RUNNING = 1
    STARTING = 2
    STOPPING = 3

@dataclass
class DuoPlusConfig:
    """DuoPlus API Configuration"""
    api_key: str
    base_url: str = "https://api.duoplus.net/api/v1"
    timeout: int = 30

class DuoPlusAPI:
    """DuoPlus Cloud Phone API Client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.duoplus.net/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = 30
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data or {}, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data or {}, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            # Check for API errors
            if result.get("code") and result.get("code") != 0:
                error_msg = result.get("message", "Unknown error")
                print(f"⚠️ API Error: {result.get('code')} - {error_msg}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return {"code": -1, "message": str(e)}
    
    # ==================== Phone Management ====================
    
    def list_phones(self, page: int = 1, page_size: int = 100, group_id: str = None) -> Dict:
        """
        Get list of cloud phones
        
        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page (max 100)
            group_id: Optional group ID to filter phones
        """
        data = {
            "page": page,
            "pageSize": page_size
        }
        if group_id:
            data["groupId"] = group_id
        
        return self._request("POST", "/phone/list", data)
    
    def get_phone_info(self, phone_id: str) -> Dict:
        """Get detailed info about a specific phone"""
        return self._request("POST", "/phone/info", {"phoneId": phone_id})
    
    def power_on(self, phone_ids: List[str]) -> Dict:
        """
        Power on cloud phones
        
        Args:
            phone_ids: List of phone IDs to power on
        """
        return self._request("POST", "/phone/powerOn", {"phoneIds": phone_ids})
    
    def power_off(self, phone_ids: List[str]) -> Dict:
        """
        Power off cloud phones
        
        Args:
            phone_ids: List of phone IDs to power off
        """
        return self._request("POST", "/phone/powerOff", {"phoneIds": phone_ids})
    
    def restart(self, phone_ids: List[str]) -> Dict:
        """Restart cloud phones"""
        return self._request("POST", "/phone/restart", {"phoneIds": phone_ids})
    
    # ==================== Proxy Management ====================
    
    def set_proxy(self, phone_id: str, proxy_type: str, proxy_host: str, proxy_port: int,
                  proxy_user: str = None, proxy_pass: str = None) -> Dict:
        """
        Set proxy for a cloud phone
        
        Args:
            phone_id: Phone ID
            proxy_type: Proxy type (http, https, socks5)
            proxy_host: Proxy host
            proxy_port: Proxy port
            proxy_user: Proxy username (optional)
            proxy_pass: Proxy password (optional)
        """
        data = {
            "phoneId": phone_id,
            "proxyType": proxy_type,
            "proxyHost": proxy_host,
            "proxyPort": proxy_port
        }
        if proxy_user:
            data["proxyUser"] = proxy_user
        if proxy_pass:
            data["proxyPass"] = proxy_pass
        
        return self._request("POST", "/phone/setProxy", data)
    
    def clear_proxy(self, phone_id: str) -> Dict:
        """Clear proxy settings for a phone"""
        return self._request("POST", "/phone/clearProxy", {"phoneId": phone_id})
    
    # ==================== File Operations ====================
    
    def upload_file(self, phone_ids: List[str], file_url: str, 
                    target_path: str = "/sdcard/DCIM/Camera/") -> Dict:
        """
        Upload file to cloud phones via URL
        
        Args:
            phone_ids: List of phone IDs
            file_url: URL of file to upload (must be publicly accessible)
            target_path: Target path on phone (default: camera directory)
        """
        data = {
            "phoneIds": phone_ids,
            "fileUrl": file_url,
            "targetPath": target_path
        }
        return self._request("POST", "/phone/uploadFile", data)
    
    def push_file(self, phone_ids: List[str], file_url: str, 
                  file_name: str = None, target_dir: str = "Camera") -> Dict:
        """
        Push file to cloud phones (alternative method)
        
        Args:
            phone_ids: List of phone IDs
            file_url: URL of file to push
            file_name: Optional custom filename
            target_dir: Target directory (Camera, Download, Documents)
        """
        data = {
            "phoneIds": phone_ids,
            "fileUrl": file_url,
            "targetDir": target_dir
        }
        if file_name:
            data["fileName"] = file_name
        
        return self._request("POST", "/file/push", data)
    
    # ==================== RPA Operations ====================
    
    def create_rpa_task(self, phone_ids: List[str], task_type: str, 
                        params: Dict = None) -> Dict:
        """
        Create RPA automation task
        
        Args:
            phone_ids: List of phone IDs
            task_type: Type of RPA task
            params: Task-specific parameters
        """
        data = {
            "phoneIds": phone_ids,
            "taskType": task_type,
            "params": params or {}
        }
        return self._request("POST", "/rpa/task/create", data)
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get status of an RPA task"""
        return self._request("POST", "/rpa/task/status", {"taskId": task_id})
    
    def list_tasks(self, page: int = 1, page_size: int = 100) -> Dict:
        """List RPA tasks"""
        return self._request("POST", "/rpa/task/list", {
            "page": page,
            "pageSize": page_size
        })
    
    # ==================== Group Management ====================
    
    def list_groups(self) -> Dict:
        """Get list of phone groups"""
        return self._request("POST", "/group/list", {})
    
    def create_group(self, name: str, description: str = "") -> Dict:
        """Create a new group"""
        return self._request("POST", "/group/create", {
            "name": name,
            "description": description
        })


class InstagramDuoPlus:
    """
    Instagram Automation Helper for DuoPlus
    
    This class provides higher-level methods for Instagram automation
    """
    
    def __init__(self, api: DuoPlusAPI):
        self.api = api
    
    def upload_video_to_phone(self, phone_id: str, video_url: str) -> bool:
        """
        Upload video to phone's camera roll
        
        Args:
            phone_id: DuoPlus phone ID
            video_url: Public URL of video file
            
        Returns:
            True if upload was initiated successfully
        """
        print(f"📤 Uploading video to phone {phone_id}...")
        result = self.api.upload_file(
            phone_ids=[phone_id],
            file_url=video_url,
            target_path="/sdcard/DCIM/Camera/"
        )
        
        if result.get("code") == 0:
            print("✅ Upload initiated successfully")
            return True
        else:
            print(f"❌ Upload failed: {result.get('message')}")
            return False
    
    def publish_reels(self, phone_id: str, video_url: str, caption: str = "",
                      hashtags: List[str] = None) -> Dict:
        """
        Publish Instagram Reels
        
        Note: This requires RPA support from DuoPlus
        
        Args:
            phone_id: Phone ID
            video_url: Video URL to upload
            caption: Reel caption
            hashtags: List of hashtags (without #)
        """
        # First upload video
        if not self.upload_video_to_phone(phone_id, video_url):
            return {"success": False, "error": "Failed to upload video"}
        
        # Wait for upload to complete
        print("⏳ Waiting for video upload...")
        time.sleep(10)  # Adjust based on video size
        
        # Build caption with hashtags
        full_caption = caption
        if hashtags:
            tags = " ".join([f"#{tag}" for tag in hashtags])
            full_caption = f"{caption}\n\n{tags}"
        
        # Create RPA task for Instagram posting
        result = self.api.create_rpa_task(
            phone_ids=[phone_id],
            task_type="instagram_post_reels",
            params={
                "caption": full_caption,
                "video_path": "/sdcard/DCIM/Camera/"
            }
        )
        
        return result


def test_connection(api_key: str):
    """Test DuoPlus API connection"""
    print("=" * 60)
    print("DuoPlus API Connection Test")
    print("=" * 60)
    
    api = DuoPlusAPI(api_key)
    
    # Test list phones
    print("\n📱 Testing phone list...")
    result = api.list_phones()
    print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 160002:
        print("\n" + "="*60)
        print("⚠️  API доступ не настроен!")
        print("="*60)
        print("""
Для активации API в DuoPlus:

1. Войдите в панель управления: https://my.duoplus.net/

2. Перейдите в настройки (Settings / 设置)

3. Найдите раздел "API Configuration" или "API Access"

4. Включите API доступ (Enable API)

5. Скопируйте новый API ключ (если изменился)

6. Убедитесь, что у вашего тарифа есть доступ к API
   (некоторые тарифы не включают API)
""")
    
    return result


if __name__ == "__main__":
    # Your DuoPlus API Key
    API_KEY = "043fd16c-b586-4292-a431-6e81f40e4402"
    
    test_connection(API_KEY)
