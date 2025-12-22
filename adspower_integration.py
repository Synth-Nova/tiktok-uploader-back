#!/usr/bin/env python3
"""
AdsPower Local API Integration
Интеграция с AdsPower для автоматизации Instagram

API Base: http://local.adspower.net:50325
Docs: https://localapi-doc-en.adspower.com/
"""

import os
import time
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AdsPowerProfile:
    """Профиль AdsPower"""
    user_id: str
    serial_number: int
    name: str
    group_id: str
    group_name: str
    domain_name: str
    username: str
    remark: str
    created_time: int
    ip: str
    ip_country: str
    fakey: str
    password: str
    last_open_time: int


class AdsPowerAPI:
    """
    AdsPower Local API Client
    
    Позволяет:
    - Управлять профилями браузера
    - Открывать/закрывать браузеры
    - Получать данные для Selenium/Puppeteer автоматизации
    """
    
    def __init__(self, api_key: str, base_url: str = "http://local.adspower.net:50325"):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ для авторизации
            base_url: Базовый URL API (локальный)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
        
        logger.info(f"AdsPower API initialized: {self.base_url}")
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Выполнить API запрос"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, json=data, params=params, timeout=30)
            
            result = response.json()
            return result
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {"code": -1, "msg": f"Connection error: AdsPower не запущен или недоступен по {self.base_url}"}
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"code": -1, "msg": str(e)}
    
    # ==================== Connection ====================
    
    def check_connection(self) -> Dict:
        """Проверить соединение с AdsPower"""
        return self._request('GET', '/status')
    
    # ==================== Profiles ====================
    
    def list_profiles(self, page: int = 1, page_size: int = 50, group_id: str = None) -> Dict:
        """
        Получить список профилей
        
        Args:
            page: Номер страницы
            page_size: Размер страницы (макс 100)
            group_id: ID группы для фильтрации
        """
        params = {
            'page': page,
            'page_size': min(page_size, 100)
        }
        if group_id:
            params['group_id'] = group_id
            
        return self._request('GET', '/api/v1/user/list', params=params)
    
    def create_profile(
        self,
        name: str,
        group_id: str = "0",
        domain_name: str = None,
        open_urls: List[str] = None,
        username: str = None,
        password: str = None,
        fakey: str = None,
        cookie: str = None,
        remark: str = None,
        proxy_config: Dict = None,
        fingerprint_config: Dict = None
    ) -> Dict:
        """
        Создать новый профиль
        
        Args:
            name: Имя профиля
            group_id: ID группы
            domain_name: Домен для автозаполнения
            open_urls: URL для открытия при старте
            username: Имя пользователя
            password: Пароль
            fakey: 2FA ключ
            cookie: Cookies
            remark: Примечание
            proxy_config: Настройки прокси
            fingerprint_config: Настройки отпечатка
        """
        data = {
            'name': name,
            'group_id': group_id
        }
        
        if domain_name:
            data['domain_name'] = domain_name
        if open_urls:
            data['open_urls'] = open_urls
        if username:
            data['username'] = username
        if password:
            data['password'] = password
        if fakey:
            data['fakey'] = fakey
        if cookie:
            data['cookie'] = cookie
        if remark:
            data['remark'] = remark
        if proxy_config:
            data['user_proxy_config'] = proxy_config
        if fingerprint_config:
            data['fingerprint_config'] = fingerprint_config
            
        return self._request('POST', '/api/v1/user/create', data=data)
    
    def delete_profile(self, user_ids: List[str]) -> Dict:
        """Удалить профили"""
        return self._request('POST', '/api/v1/user/delete', data={'user_ids': user_ids})
    
    def query_profile(self, user_id: str = None, serial_number: int = None) -> Dict:
        """Получить информацию о профиле"""
        params = {}
        if user_id:
            params['user_id'] = user_id
        if serial_number:
            params['serial_number'] = serial_number
        return self._request('GET', '/api/v1/user/info', params=params)
    
    # ==================== Browser ====================
    
    def start_browser(
        self,
        user_id: str = None,
        serial_number: int = None,
        open_tabs: int = 0,
        ip_tab: int = 0,
        headless: int = 0,
        launch_args: List[str] = None
    ) -> Dict:
        """
        Запустить браузер
        
        Args:
            user_id: ID профиля
            serial_number: Серийный номер профиля
            open_tabs: Открывать вкладки (0=да, 1=нет)
            ip_tab: Открывать страницу проверки IP (0=нет, 1=да)
            headless: Режим без интерфейса (0=нет, 1=да)
            launch_args: Дополнительные аргументы запуска
            
        Returns:
            Dict с данными для Selenium/Puppeteer подключения:
            - ws.selenium: адрес для Selenium
            - ws.puppeteer: адрес для Puppeteer
            - webdriver: путь к chromedriver
        """
        params = {
            'open_tabs': open_tabs,
            'ip_tab': ip_tab,
            'headless': headless
        }
        
        if user_id:
            params['user_id'] = user_id
        elif serial_number:
            params['serial_number'] = serial_number
        else:
            return {"code": -1, "msg": "user_id or serial_number required"}
        
        if launch_args:
            params['launch_args'] = json.dumps(launch_args)
            
        return self._request('GET', '/api/v1/browser/start', params=params)
    
    def stop_browser(self, user_id: str = None, serial_number: int = None) -> Dict:
        """Закрыть браузер"""
        params = {}
        if user_id:
            params['user_id'] = user_id
        elif serial_number:
            params['serial_number'] = serial_number
        return self._request('GET', '/api/v1/browser/stop', params=params)
    
    def check_browser_status(self, user_id: str = None, serial_number: int = None) -> Dict:
        """Проверить статус браузера"""
        params = {}
        if user_id:
            params['user_id'] = user_id
        elif serial_number:
            params['serial_number'] = serial_number
        return self._request('GET', '/api/v1/browser/active', params=params)
    
    # ==================== Groups ====================
    
    def list_groups(self, page: int = 1, page_size: int = 100) -> Dict:
        """Получить список групп"""
        return self._request('GET', '/api/v1/group/list', params={
            'page': page,
            'page_size': page_size
        })
    
    def create_group(self, group_name: str, remark: str = None) -> Dict:
        """Создать группу"""
        data = {'group_name': group_name}
        if remark:
            data['remark'] = remark
        return self._request('POST', '/api/v1/group/create', data=data)
    
    # ==================== Proxy ====================
    
    @staticmethod
    def create_proxy_config(
        proxy_type: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None,
        proxy_soft: str = "other"
    ) -> Dict:
        """
        Создать конфигурацию прокси
        
        Args:
            proxy_type: Тип прокси (http, https, socks5)
            host: Хост прокси
            port: Порт
            username: Логин
            password: Пароль
            proxy_soft: Софт прокси (luminati, oxylabs, other)
        """
        config = {
            "proxy_type": proxy_type,
            "proxy_host": host,
            "proxy_port": str(port),
            "proxy_soft": proxy_soft
        }
        
        if username:
            config["proxy_user"] = username
        if password:
            config["proxy_password"] = password
            
        return config


class InstagramAdsPower:
    """
    Помощник для автоматизации Instagram через AdsPower + Selenium
    """
    
    def __init__(self, api: AdsPowerAPI):
        self.api = api
        self.driver = None
        self.current_profile = None
    
    def setup_instagram_profile(
        self,
        name: str,
        proxy_type: str = "http",
        proxy_host: str = None,
        proxy_port: int = None,
        proxy_user: str = None,
        proxy_pass: str = None,
        cookies: str = None
    ) -> Dict:
        """
        Создать профиль для Instagram
        
        Args:
            name: Имя профиля
            proxy_*: Настройки прокси
            cookies: Instagram cookies (JSON строка)
        """
        proxy_config = None
        if proxy_host and proxy_port:
            proxy_config = self.api.create_proxy_config(
                proxy_type=proxy_type,
                host=proxy_host,
                port=proxy_port,
                username=proxy_user,
                password=proxy_pass
            )
        
        return self.api.create_profile(
            name=f"IG_{name}",
            domain_name="instagram.com",
            open_urls=["https://www.instagram.com/"],
            cookie=cookies,
            proxy_config=proxy_config,
            remark=f"Instagram account: {name}"
        )
    
    def connect_selenium(self, user_id: str) -> Any:
        """
        Подключиться к браузеру через Selenium
        
        Args:
            user_id: ID профиля
            
        Returns:
            Selenium WebDriver
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Запускаем браузер
        result = self.api.start_browser(
            user_id=user_id,
            ip_tab=0,
            open_tabs=1
        )
        
        if result.get('code') != 0:
            raise Exception(f"Failed to start browser: {result.get('msg')}")
        
        data = result.get('data', {})
        selenium_address = data.get('ws', {}).get('selenium')
        webdriver_path = data.get('webdriver')
        
        if not selenium_address:
            raise Exception("No selenium address in response")
        
        # Подключаемся к браузеру
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", selenium_address)
        
        service = Service(webdriver_path) if webdriver_path else None
        
        self.driver = webdriver.Chrome(options=chrome_options, service=service)
        self.current_profile = user_id
        
        return self.driver
    
    def post_reels(
        self,
        video_path: str,
        caption: str,
        hashtags: List[str] = None
    ) -> bool:
        """
        Опубликовать Reels в Instagram
        
        Args:
            video_path: Путь к видео файлу
            caption: Описание
            hashtags: Хэштеги
            
        Returns:
            True если успешно
        """
        if not self.driver:
            raise Exception("Browser not connected. Call connect_selenium first.")
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        import time
        
        driver = self.driver
        
        try:
            # Формируем полный caption
            full_caption = caption
            if hashtags:
                tags = ' '.join(f'#{tag}' for tag in hashtags)
                full_caption = f"{caption}\n\n{tags}"
            
            # Переходим на Instagram
            driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Нажимаем на кнопку создания поста (+)
            create_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Create')]//ancestor::a | //*[@aria-label='New post']"))
            )
            create_btn.click()
            time.sleep(2)
            
            # Загружаем видео
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(video_path))
            time.sleep(5)
            
            # Нажимаем Next
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Next']"))
            )
            next_btn.click()
            time.sleep(2)
            
            # Ещё раз Next (редактирование)
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Next']"))
            )
            next_btn.click()
            time.sleep(2)
            
            # Вводим caption
            caption_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@aria-label='Write a caption...']"))
            )
            caption_input.send_keys(full_caption)
            time.sleep(1)
            
            # Публикуем
            share_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Share']"))
            )
            share_btn.click()
            
            # Ждём завершения
            time.sleep(10)
            
            logger.info("Reels posted successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error posting reels: {e}")
            return False
    
    def close(self):
        """Закрыть браузер"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        if self.current_profile:
            self.api.stop_browser(user_id=self.current_profile)
            self.current_profile = None


# ==================== Test ====================

def test_connection():
    """Тест подключения к AdsPower"""
    
    API_KEY = "c598bb647cfad0b667d73002a392c94e"
    BASE_URL = "http://local.adspower.net:50325"
    
    print("=" * 50)
    print("🔌 AdsPower Connection Test")
    print("=" * 50)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Base URL: {BASE_URL}")
    print()
    
    api = AdsPowerAPI(api_key=API_KEY, base_url=BASE_URL)
    
    # Проверяем соединение
    print("📡 Проверка соединения...")
    status = api.check_connection()
    print(f"   Ответ: {status}")
    
    if status.get('code') == 0:
        print("   ✅ AdsPower работает!")
    else:
        print(f"   ❌ Ошибка: {status.get('msg')}")
        print("\n   ⚠️  Убедитесь что:")
        print("   1. AdsPower запущен на вашем компьютере")
        print("   2. Local API включен в настройках")
        print("   3. Порт 50325 доступен")
        return False
    
    # Получаем список профилей
    print("\n📋 Получение списка профилей...")
    profiles = api.list_profiles(page=1, page_size=10)
    
    if profiles.get('code') == 0:
        data = profiles.get('data', {})
        items = data.get('list', [])
        print(f"   ✅ Найдено профилей: {len(items)}")
        
        for p in items[:5]:
            print(f"   - {p.get('name')} (ID: {p.get('user_id')}, Serial: {p.get('serial_number')})")
    else:
        print(f"   ❌ Ошибка: {profiles.get('msg')}")
    
    # Получаем группы
    print("\n📁 Получение групп...")
    groups = api.list_groups()
    
    if groups.get('code') == 0:
        items = groups.get('data', {}).get('list', [])
        print(f"   ✅ Найдено групп: {len(items)}")
        for g in items[:5]:
            print(f"   - {g.get('group_name')} (ID: {g.get('group_id')})")
    
    print("\n" + "=" * 50)
    print("✅ Тест завершён!")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    test_connection()
