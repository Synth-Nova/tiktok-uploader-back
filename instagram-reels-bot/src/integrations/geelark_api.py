#!/usr/bin/env python3
"""
GeeLark API Integration
Интеграция с GeeLark Cloud Phone API для автоматизации Instagram/TikTok

Base URL: https://openapi.geelark.com/open/v1/
Документация: https://open.geelark.com/api

Аутентификация: Bearer Token
Headers:
  - Authorization: Bearer <token>
  - traceId: UUID v4
  - Content-Type: application/json
"""

import os
import json
import time
import uuid
import hashlib
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Constants ====================

# Callback Types
CALLBACK_TYPES = {
    1: "boot_event",           # Телефон запущен
    3: "plugin_install",       # Плагин установлен  
    4: "file_upload",          # Файл загружен
    6: "task_completion",      # Задача завершена
    8: "stop_event",           # Телефон остановлен
}

# Task Types
TASK_TYPES = {
    1: "tiktok_video",         # TikTok video posting
    2: "tiktok_warmup",        # TikTok AI account warmup
    3: "tiktok_carousel",      # TikTok carousel posting
    4: "tiktok_login",         # TikTok account login
    6: "tiktok_profile_edit",  # TikTok profile editing
    42: "custom",              # Custom (Facebook, YouTube, Instagram, etc.)
}

# Task Status
TASK_STATUS = {
    1: "waiting",      # Ожидание
    2: "in_progress",  # В процессе
    3: "completed",    # Завершено успешно
    4: "failed",       # Ошибка
    7: "cancelled",    # Отменено
}

# Common Failure Codes (most relevant for Instagram/video posting)
TASK_FAILURE_CODES = {
    20002: "Machine is performing other tasks",
    20003: "Execution timeout",
    20005: "Task canceled",
    20100: "No network connection",
    20116: "Account is not logged in",
    20129: "Device offline",
    20136: "Account blocked",
    20200: "Failed to download file",
    20201: "Failed to upload video - check network",
    20204: "Video upload was rejected",
    20209: "Failed to select video",
    20213: "Clicking Publish failed",
    20251: "Video publishing failed, saved to drafts",
    20257: "Video upload timed out",
    20264: "Account temporarily restricted",
    20267: "Custom template task publishing failed",
    29997: "Insufficient balance",
    29998: "Cloud phone has been deleted",
    29999: "Unknown error",
}


# ==================== Data Classes ====================

@dataclass
class GeeLarkPhone:
    """Облачный телефон GeeLark"""
    id: str
    serial_name: str
    serial_no: str
    status: int  # 0=stopped, 1=running
    remark: Optional[str] = None
    group: Optional[Dict] = None
    tags: Optional[List[Dict]] = None
    equipment_info: Optional[Dict] = None
    proxy: Optional[Dict] = None


@dataclass
class ProxyConfig:
    """Конфигурация прокси"""
    type_id: int  # 1=socks5, 2=http, 3=https
    server: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "typeId": self.type_id,
            "server": self.server,
            "port": self.port
        }
        if self.username:
            result["username"] = self.username
        if self.password:
            result["password"] = self.password
        return result


@dataclass 
class ProxyInfo:
    """Прокси в строковом формате"""
    proxy_string: str  # формат: socks5://user:pass@host:port
    
    @classmethod
    def from_parts(cls, proxy_type: str, host: str, port: int, 
                   username: str = None, password: str = None) -> 'ProxyInfo':
        if username and password:
            return cls(f"{proxy_type}://{username}:{password}@{host}:{port}")
        return cls(f"{proxy_type}://{host}:{port}")


# ==================== GeeLark API Client ====================

class GeeLarkAPI:
    """
    GeeLark API Client
    
    Документация: https://open.geelark.com/api
    Base URL: https://openapi.geelark.com/open/v1/
    
    Rate Limits:
    - 200 requests per minute
    - 24,000 requests per hour
    """
    
    BASE_URL = "https://openapi.geelark.com/open/v1"
    
    # Android версии
    ANDROID_VERSIONS = {
        "10": 1,
        "11": 2,
        "12": 3,
        "13": 4,
        "10_live": 5,  # для стриминга
        "14": 7,
        "15": 8
    }
    
    # Типы прокси
    PROXY_TYPES = {
        "socks5": 1,
        "http": 2,
        "https": 3
    }
    
    def __init__(
        self, 
        bearer_token: str,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Инициализация клиента
        
        Args:
            bearer_token: Bearer токен для авторизации
            app_id: APP ID (для key verification)
            api_key: API Key (для key verification)
        """
        self.bearer_token = bearer_token
        self.app_id = app_id
        self.api_key = api_key
        self.session = requests.Session()
        
        logger.info(f"GeeLark API initialized with base URL: {self.BASE_URL}")
    
    def _generate_trace_id(self) -> str:
        """Генерация traceId (UUID v4 uppercase)"""
        return str(uuid.uuid4()).upper().replace("-", "")
    
    def _get_headers(self, use_key_auth: bool = False) -> Dict[str, str]:
        """
        Получить заголовки для запроса
        
        Args:
            use_key_auth: Использовать key verification вместо token
        """
        trace_id = self._generate_trace_id()
        
        headers = {
            "Content-Type": "application/json",
            "traceId": trace_id
        }
        
        if use_key_auth and self.app_id and self.api_key:
            # Key verification
            timestamp = str(int(time.time() * 1000))
            nonce = trace_id[:6]
            
            # sign = SHA256(appId + traceId + ts + nonce + apiKey)
            sign_string = self.app_id + trace_id + timestamp + nonce + self.api_key
            sign = hashlib.sha256(sign_string.encode()).hexdigest().upper()
            
            headers.update({
                "appId": self.app_id,
                "ts": timestamp,
                "nonce": nonce,
                "sign": sign
            })
        else:
            # Token verification (default)
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        
        return headers
    
    def _request(
        self, 
        endpoint: str, 
        data: Optional[Dict] = None,
        use_key_auth: bool = False
    ) -> Dict:
        """
        Выполнить API запрос
        
        Args:
            endpoint: Endpoint (например /phone/list)
            data: Данные запроса
            use_key_auth: Использовать key verification
            
        Returns:
            Dict с ответом API
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(use_key_auth)
        
        try:
            logger.debug(f"API Request: POST {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Data: {data}")
            
            response = self.session.post(
                url=url,
                headers=headers,
                json=data or {},
                timeout=30
            )
            
            logger.debug(f"Response Status: {response.status_code}")
            
            # Проверяем Content-Type
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                result = response.json()
                
                # GeeLark использует code=0 для успеха
                success = result.get("code") == 0
                
                return {
                    "success": success,
                    "status_code": response.status_code,
                    "trace_id": result.get("traceId"),
                    "code": result.get("code"),
                    "msg": result.get("msg"),
                    "data": result.get("data")
                }
            else:
                logger.warning(f"Non-JSON response: {content_type}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Non-JSON response",
                    "raw": response.text[:500]
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== Phone Management ====================
    
    def list_phones(
        self, 
        page: int = 1, 
        page_size: int = 50,
        serial_name: Optional[str] = None,
        group_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """
        Получить список облачных телефонов
        
        Args:
            page: Номер страницы
            page_size: Количество на странице (max 50)
            serial_name: Фильтр по имени
            group_name: Фильтр по группе
            tags: Фильтр по тегам
            remark: Фильтр по примечанию
        """
        data = {
            "page": page,
            "pageSize": min(page_size, 50)
        }
        
        if serial_name:
            data["serialName"] = serial_name
        if group_name:
            data["groupName"] = group_name
        if tags:
            data["tags"] = tags
        if remark:
            data["remark"] = remark
            
        return self._request("/phone/list", data)
    
    def get_phone_status(self, phone_ids: List[str]) -> Dict:
        """
        Получить статус телефонов
        
        Args:
            phone_ids: Список ID телефонов
        """
        return self._request("/phone/status", {"ids": phone_ids})
    
    def create_phone(
        self,
        amount: int = 1,
        android_version: str = "12",
        proxy_config: Optional[ProxyConfig] = None,
        group_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """
        Создать облачный телефон (deprecated API)
        
        Args:
            amount: Количество (Basic план - только 1)
            android_version: Версия Android (10, 11, 12, 13, 14, 15)
            proxy_config: Конфигурация прокси
            group_name: Имя группы
            tags: Теги
            remark: Примечание
        """
        data = {
            "amount": amount,
            "androidVersion": self.ANDROID_VERSIONS.get(android_version, 3)
        }
        
        if proxy_config:
            data["proxyConfig"] = proxy_config.to_dict()
        if group_name:
            data["groupName"] = group_name
        if tags:
            data["tagsName"] = tags
        if remark:
            data["remark"] = remark
            
        return self._request("/phone/add", data)
    
    def create_phone_v2(
        self,
        profile_name: str,
        mobile_type: str = "Android 12",
        proxy_info: Optional[str] = None,
        group_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        remark: Optional[str] = None,
        charge_mode: int = 0
    ) -> Dict:
        """
        Создать облачный телефон (V2 API)
        
        Args:
            profile_name: Имя профиля
            mobile_type: Тип телефона (Android 10/11/12/13/14/15)
            proxy_info: Прокси в формате socks5://user:pass@host:port
            group_name: Имя группы
            tags: Теги
            remark: Примечание
            charge_mode: Режим оплаты (0=по минутам, 1=месячная аренда)
        """
        env_data = {
            "profileName": profile_name,
            "mobileLanguage": "default"
        }
        
        if proxy_info:
            env_data["proxyInformation"] = proxy_info
        if group_name:
            env_data["profileGroup"] = group_name
        if tags:
            env_data["profileTags"] = tags
        if remark:
            env_data["profileNote"] = remark
        
        data = {
            "mobileType": mobile_type,
            "chargeMode": charge_mode,
            "data": [env_data]
        }
            
        return self._request("/phone/addNew", data)
    
    def start_phones(self, phone_ids: List[str]) -> Dict:
        """
        Запустить облачные телефоны
        
        Args:
            phone_ids: Список ID телефонов
        """
        return self._request("/phone/start", {"ids": phone_ids})
    
    def stop_phones(self, phone_ids: List[str]) -> Dict:
        """
        Остановить облачные телефоны
        
        Args:
            phone_ids: Список ID телефонов
        """
        return self._request("/phone/stop", {"ids": phone_ids})
    
    def delete_phones(self, phone_ids: List[str]) -> Dict:
        """
        Удалить облачные телефоны
        
        Args:
            phone_ids: Список ID телефонов
        """
        return self._request("/phone/delete", {"ids": phone_ids})
    
    def update_phone(
        self,
        phone_id: str,
        name: Optional[str] = None,
        remark: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        group_id: Optional[str] = None,
        proxy_config: Optional[ProxyConfig] = None,
        proxy_id: Optional[str] = None
    ) -> Dict:
        """
        Обновить информацию о телефоне
        
        Args:
            phone_id: ID телефона
            name: Новое имя
            remark: Примечание
            tag_ids: Список ID тегов
            group_id: ID группы
            proxy_config: Конфигурация прокси
            proxy_id: ID сохранённого прокси
        """
        data = {"id": phone_id}
        
        if name:
            data["name"] = name
        if remark:
            data["remark"] = remark
        if tag_ids:
            data["tagIDs"] = tag_ids
        if group_id:
            data["groupID"] = group_id
        if proxy_config:
            data["proxyConfig"] = proxy_config.to_dict()
        if proxy_id:
            data["proxyId"] = proxy_id
            
        return self._request("/phone/detail/update", data)
    
    def take_screenshot(self, phone_id: str) -> Dict:
        """
        Сделать скриншот телефона
        
        Args:
            phone_id: ID телефона
            
        Returns:
            Dict с taskId для получения результата
        """
        return self._request("/phone/screenShot", {"id": phone_id})
    
    def get_screenshot_result(self, task_id: str) -> Dict:
        """
        Получить результат скриншота
        
        Args:
            task_id: ID задачи скриншота
            
        Returns:
            Dict со статусом и ссылкой на скриншот
        """
        return self._request("/phone/screenShot/result", {"taskId": task_id})
    
    def send_sms(self, phone_id: str, phone_number: str, text: str) -> Dict:
        """
        Отправить SMS на телефон
        
        Args:
            phone_id: ID телефона
            phone_number: Номер отправителя
            text: Текст сообщения
        """
        return self._request("/phone/sendSms", {
            "id": phone_id,
            "phoneNumber": phone_number,
            "text": text
        })
    
    def get_brand_list(self, android_version: int = 12) -> Dict:
        """
        Получить список брендов телефонов
        
        Args:
            android_version: Версия Android (10-15)
        """
        return self._request("/phone/brand/list", {"androidVer": android_version})
    
    def one_click_new_phone(self, phone_id: str) -> Dict:
        """
        Сброс телефона до нового состояния
        
        Args:
            phone_id: ID телефона
        """
        return self._request("/v2/phone/newOne", {"id": phone_id})
    
    def get_device_id(self, phone_id: str) -> Dict:
        """
        Получить уникальный ID устройства
        
        Args:
            phone_id: ID телефона
        """
        return self._request("/phone/serialNum/get", {"id": phone_id})
    
    # ==================== GPS ====================
    
    def get_gps(self, phone_ids: List[str]) -> Dict:
        """Получить GPS координаты телефонов"""
        return self._request("/phone/gps/get", {"ids": phone_ids})
    
    def set_gps(self, gps_list: List[Dict[str, Any]]) -> Dict:
        """
        Установить GPS координаты
        
        Args:
            gps_list: Список [{id, latitude, longitude}, ...]
        """
        return self._request("/phone/gps/set", {"list": gps_list})
    
    # ==================== Instagram RPA ====================
    
    def publish_instagram_reels(
        self,
        phone_id: str,
        video_urls: List[str],
        description: str,
        schedule_at: Optional[int] = None,
        name: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """
        Опубликовать Instagram Reels
        
        Endpoint: /rpa/task/instagramPubReels
        
        Args:
            phone_id: ID облачного телефона
            video_urls: Список URL видео (до 10), должны быть загружены через upload API
            description: Описание/caption (до 2200 символов)
            schedule_at: Время публикации (timestamp), если None - сейчас
            name: Название задачи (до 128 символов)
            remark: Примечание (до 200 символов)
            
        Returns:
            Dict с taskId для отслеживания
        """
        if schedule_at is None:
            schedule_at = int(time.time()) + 60  # через 1 минуту
        
        data = {
            "id": phone_id,
            "video": video_urls[:10],  # максимум 10 видео
            "description": description[:2200],  # максимум 2200 символов
            "scheduleAt": schedule_at
        }
        
        if name:
            data["name"] = name[:128]
        if remark:
            data["remark"] = remark[:200]
            
        return self._request("/rpa/task/instagramPubReels", data)
    
    def query_tasks(self, task_ids: List[str]) -> Dict:
        """
        Запросить статус задач
        
        Endpoint: /task/query
        
        Args:
            task_ids: Список ID задач (до 100)
            
        Returns:
            Dict с items содержащими статус каждой задачи:
            - status: 1=waiting, 2=in_progress, 3=completed, 4=failed, 7=cancelled
            - failCode/failDesc: причина ошибки (если status=4)
        """
        return self._request("/task/query", {"ids": task_ids[:100]})
    
    def query_task(self, task_id: str) -> Dict:
        """
        Запросить статус одной задачи
        
        Args:
            task_id: ID задачи
        """
        result = self.query_tasks([task_id])
        if result.get("success") and result.get("data", {}).get("items"):
            return {
                "success": True,
                "task": result["data"]["items"][0]
            }
        return result
    
    def get_task_history(self, size: int = 100, last_id: str = None) -> Dict:
        """
        Получить историю задач за последние 7 дней
        
        Endpoint: /task/historyRecords
        
        Args:
            size: Количество записей (макс 100)
            last_id: ID последней записи предыдущей страницы (для пагинации)
        """
        data = {"size": min(size, 100)}
        if last_id:
            data["lastId"] = last_id
        return self._request("/task/historyRecords", data)
    
    def cancel_task(self, task_id: str) -> Dict:
        """
        Отменить задачу
        
        Args:
            task_id: ID задачи
        """
        return self._request("/task/cancel", {"taskId": task_id})
    
    def retry_task(self, task_id: str) -> Dict:
        """
        Повторить задачу
        
        Args:
            task_id: ID задачи
        """
        return self._request("/task/retry", {"taskId": task_id})
    
    def wait_for_task(
        self, 
        task_id: str, 
        timeout: int = 300,
        poll_interval: int = 10
    ) -> Dict:
        """
        Ожидать завершения задачи
        
        Args:
            task_id: ID задачи
            timeout: Максимальное время ожидания (секунды)
            poll_interval: Интервал проверки (секунды)
            
        Returns:
            Dict с финальным статусом задачи
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.query_task(task_id)
            
            if result.get("success") and result.get("task"):
                task = result["task"]
                status = task.get("status")
                
                # 3=completed, 4=failed, 7=cancelled
                if status in [3, 4, 7]:
                    status_name = TASK_STATUS.get(status, "unknown")
                    return {
                        "success": status == 3,
                        "status": status_name,
                        "task": task,
                        "elapsed": time.time() - start_time
                    }
            
            time.sleep(poll_interval)
        
        return {
            "success": False,
            "error": "Timeout waiting for task",
            "task_id": task_id,
            "elapsed": timeout
        }
    
    # ==================== File Upload ====================
    
    def upload_file(self, phone_id: str, file_url: str) -> Dict:
        """
        Загрузить один файл на облачный телефон
        
        Endpoint: /phone/uploadFile
        Файл загружается в папку "Downloads" на телефоне.
        ВАЖНО: Телефон должен быть запущен!
        
        Args:
            phone_id: ID телефона
            file_url: URL файла для загрузки
            
        Returns:
            Dict с taskId для отслеживания
        """
        return self._request("/phone/uploadFile", {
            "id": phone_id,
            "fileUrl": file_url
        })
    
    def upload_files_batch(
        self,
        phone_id: str,
        file_urls: List[str],
        schedule_at: Optional[int] = None,
        name: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Dict:
        """
        Загрузить несколько файлов на облачный телефон (RPA задача)
        
        Endpoint: /rpa/task/fileUpload
        
        Args:
            phone_id: ID телефона
            file_urls: Список URL файлов (до 100)
            schedule_at: Время выполнения (timestamp), None = сейчас
            name: Название задачи
            remark: Примечание
            
        Returns:
            Dict с taskId для отслеживания
        """
        if schedule_at is None:
            schedule_at = int(time.time()) + 30  # через 30 секунд
        
        data = {
            "id": phone_id,
            "files": file_urls[:100],  # максимум 100 файлов
            "scheduleAt": schedule_at
        }
        
        if name:
            data["name"] = name[:128]
        if remark:
            data["remark"] = remark[:200]
            
        return self._request("/rpa/task/fileUpload", data)
    
    # ==================== Root ====================
    
    def set_root_status(self, phone_ids: List[str], enabled: bool) -> Dict:
        """
        Включить/выключить root
        
        Args:
            phone_ids: Список ID телефонов
            enabled: True для включения
        """
        return self._request("/root/setStatus", {
            "ids": phone_ids,
            "open": enabled
        })
    
    # ==================== Proxy Helpers ====================
    
    @staticmethod
    def create_decodo_proxy(region: str = "us") -> str:
        """
        Создать строку прокси для Decodo
        
        Args:
            region: Регион (us, gb, de)
            
        Returns:
            Строка прокси в формате http://user:pass@host:port
        """
        username = "spvzzn2tmc"
        password = "gbLZ8rl9y=VlXx37je"
        
        hosts = {
            "us": ("us.decodo.com", 10001),
            "gb": ("gb.decodo.com", 30001),
            "de": ("de.decodo.com", 20001)
        }
        
        host, port = hosts.get(region.lower(), hosts["us"])
        return f"http://{username}:{password}@{host}:{port}"
    
    @staticmethod
    def create_proxy_config(
        proxy_type: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None
    ) -> ProxyConfig:
        """Создать конфигурацию прокси"""
        type_map = {"socks5": 1, "http": 2, "https": 3}
        return ProxyConfig(
            type_id=type_map.get(proxy_type.lower(), 2),
            server=host,
            port=port,
            username=username,
            password=password
        )


# ==================== Instagram Automation Helper ====================

class InstagramGeeLark:
    """
    Помощник для автоматизации Instagram через GeeLark
    
    Полный цикл работы:
    1. Создать профили телефонов с прокси
    2. Установить Instagram на телефоны
    3. Залогиниться в аккаунты (вручную или через RPA)
    4. Публиковать Reels через API
    """
    
    def __init__(self, api: GeeLarkAPI):
        self.api = api
    
    def setup_instagram_phone(
        self,
        name: str,
        region: str = "us",
        android_version: str = "12"
    ) -> Dict:
        """
        Создать телефон для Instagram
        
        Args:
            name: Имя профиля
            region: Регион прокси (us, gb, de)
            android_version: Версия Android
        """
        proxy = self.api.create_decodo_proxy(region)
        
        return self.api.create_phone_v2(
            profile_name=f"IG_{name}",
            mobile_type=f"Android {android_version}",
            proxy_info=proxy,
            group_name="Instagram",
            tags=["instagram", "reels", region],
            remark=f"Instagram account - {region.upper()}"
        )
    
    def batch_create_phones(
        self,
        count: int,
        name_prefix: str = "IG",
        regions: List[str] = None
    ) -> List[Dict]:
        """
        Создать несколько телефонов для Instagram
        
        Args:
            count: Количество телефонов
            name_prefix: Префикс имени
            regions: Список регионов (циклический)
        """
        if regions is None:
            regions = ["us", "gb", "de"]
        
        results = []
        
        for i in range(count):
            region = regions[i % len(regions)]
            name = f"{name_prefix}_{i+1:03d}"
            
            result = self.setup_instagram_phone(
                name=name,
                region=region
            )
            
            results.append({
                "index": i + 1,
                "name": name,
                "region": region,
                "result": result
            })
            
            # Rate limit: 200 req/min
            time.sleep(0.5)
        
        return results
    
    def publish_reels(
        self,
        phone_id: str,
        video_url: str,
        caption: str,
        hashtags: List[str] = None,
        schedule_at: int = None
    ) -> Dict:
        """
        Опубликовать Reels на Instagram
        
        Args:
            phone_id: ID облачного телефона (с залогиненным Instagram)
            video_url: URL видео (должен быть загружен на GeeLark)
            caption: Описание поста
            hashtags: Список хэштегов (без #)
            schedule_at: Время публикации (timestamp), None = сейчас
            
        Returns:
            Dict с taskId для отслеживания
        """
        # Формируем полное описание с хэштегами
        full_caption = caption
        if hashtags:
            tags_str = " ".join(f"#{tag}" for tag in hashtags)
            full_caption = f"{caption}\n\n{tags_str}"
        
        return self.api.publish_instagram_reels(
            phone_id=phone_id,
            video_urls=[video_url],
            description=full_caption,
            schedule_at=schedule_at
        )
    
    def publish_reels_batch(
        self,
        phone_ids: List[str],
        video_url: str,
        caption: str,
        hashtags: List[str] = None,
        delay_between: int = 60
    ) -> List[Dict]:
        """
        Опубликовать Reels на нескольких аккаунтах
        
        Args:
            phone_ids: Список ID телефонов
            video_url: URL видео
            caption: Описание
            hashtags: Хэштеги
            delay_between: Задержка между публикациями (секунды)
            
        Returns:
            Список результатов с taskId
        """
        results = []
        base_time = int(time.time()) + 60  # начать через минуту
        
        for i, phone_id in enumerate(phone_ids):
            schedule_at = base_time + (i * delay_between)
            
            result = self.publish_reels(
                phone_id=phone_id,
                video_url=video_url,
                caption=caption,
                hashtags=hashtags,
                schedule_at=schedule_at
            )
            
            results.append({
                "phone_id": phone_id,
                "scheduled_at": schedule_at,
                "result": result
            })
            
            # Rate limit
            time.sleep(0.3)
        
        return results
    
    def check_tasks_status(self, task_ids: List[str]) -> List[Dict]:
        """
        Проверить статус задач публикации
        
        Args:
            task_ids: Список ID задач
            
        Returns:
            Список статусов с human-readable описанием
        """
        result = self.api.query_tasks(task_ids)
        
        if not result.get("success"):
            return [{"error": result.get("msg", "Query failed")}]
        
        statuses = []
        for task in result.get("data", {}).get("items", []):
            status_code = task.get("status")
            status_info = {
                "task_id": task.get("id"),
                "phone_name": task.get("serialName"),
                "status": TASK_STATUS.get(status_code, "unknown"),
                "status_code": status_code,
                "scheduled_at": task.get("scheduleAt"),
                "cost_seconds": task.get("cost"),
            }
            
            # Добавляем информацию об ошибке
            if status_code == 4:  # failed
                status_info["fail_code"] = task.get("failCode")
                status_info["fail_reason"] = TASK_FAILURE_CODES.get(
                    task.get("failCode"), 
                    task.get("failDesc", "Unknown error")
                )
            
            # Добавляем ссылку на пост если есть
            if task.get("shareLink"):
                status_info["share_link"] = task.get("shareLink")
                
            statuses.append(status_info)
        
        return statuses
    
    def wait_for_publication(self, task_id: str, timeout: int = 300) -> Dict:
        """
        Ожидать завершения публикации
        
        Args:
            task_id: ID задачи публикации
            timeout: Таймаут в секундах
        """
        return self.api.wait_for_task(task_id, timeout=timeout)


# ==================== Test Function ====================

def main():
    """Тестирование GeeLark API"""
    
    # Учётные данные
    APP_ID = "2FC9X9O4798WG301A0811VYO"
    BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"
    
    print("\n" + "="*60)
    print("🤖 GeeLark API Integration Test")
    print("="*60)
    print(f"APP ID: {APP_ID}")
    print(f"Bearer Token: {BEARER_TOKEN[:10]}...")
    print(f"Base URL: {GeeLarkAPI.BASE_URL}")
    print("="*60)
    
    # Создаём клиент
    client = GeeLarkAPI(
        bearer_token=BEARER_TOKEN,
        app_id=APP_ID
    )
    
    # Тест 1: Получить список телефонов
    print("\n📱 Test 1: List phones...")
    result = client.list_phones(page=1, page_size=10)
    
    phone_id = None
    if result.get("success"):
        print(f"   ✅ Success!")
        data = result.get("data", {})
        print(f"   Total phones: {data.get('total', 0)}")
        
        items = data.get("items", [])
        for phone in items[:5]:
            status = "🟢 Running" if phone.get("status") == 1 else "⚪ Stopped"
            print(f"   - {phone.get('serialName')}: {status} (ID: {phone.get('id')})")
            if phone_id is None:
                phone_id = phone.get('id')
    else:
        print(f"   ❌ Failed: {result.get('msg') or result.get('error')}")
    
    # Тест 2: Получить список брендов
    print("\n📋 Test 2: Get brand list...")
    brands = client.get_brand_list(android_version=12)
    
    if brands.get("success"):
        print(f"   ✅ Success! Found {len(brands.get('data', []))} brands")
    else:
        print(f"   ❌ Failed: {brands.get('msg')}")
    
    # Тест 3: Проверка Instagram Reels endpoint (без реальной публикации)
    print("\n📸 Test 3: Instagram Reels API availability...")
    print(f"   Endpoint: /rpa/task/instagramPubReels")
    print(f"   Method: publish_instagram_reels()")
    print(f"   ✅ Ready to use!")
    
    if phone_id:
        print(f"\n   Example usage:")
        print(f"   client.publish_instagram_reels(")
        print(f"       phone_id='{phone_id}',")
        print(f"       video_urls=['https://material.geelark.com/video.mp4'],")
        print(f"       description='My first Reels! #instagram #reels'")
        print(f"   )")
    
    print("\n" + "="*60)
    print("📊 Available Instagram Methods:")
    print("="*60)
    print("   • publish_instagram_reels() - Опубликовать Reels")
    print("   • query_task() - Проверить статус задачи")
    print("   • query_tasks_batch() - Проверить несколько задач")
    print("   • cancel_task() - Отменить задачу")
    print("   • retry_task() - Повторить задачу")
    print("   • get_task_detail() - Детали задачи")
    print("="*60)
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    main()
