#!/usr/bin/env python3
"""
Тест загрузки видео на GeeLark телефон и публикации Reels

Порядок действий:
1. Загрузить видео на публичный хостинг (file.io)
2. Запустить телефон (если не запущен)
3. Загрузить видео на телефон через API
4. Дождаться завершения загрузки
5. Опубликовать Reels
"""

import os
import sys
import time
import requests

# Добавляем путь к модулям
sys.path.insert(0, '/home/user/webapp/instagram-reels-bot/src')
from integrations.geelark_api import GeeLarkAPI, TASK_STATUS, TASK_FAILURE_CODES

# Учётные данные GeeLark
APP_ID = "2FC9X9O4798WG301A0811VYO"
BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"

# ID телефона (из предыдущей сессии)
PHONE_ID = "597099542109749349"

def upload_to_fileio(filepath: str) -> str:
    """Загрузить файл на file.io и получить публичный URL"""
    print(f"\n📤 Загрузка {filepath} на file.io...")
    
    with open(filepath, 'rb') as f:
        response = requests.post(
            'https://file.io',
            files={'file': f},
            data={'expires': '1d'}  # ссылка действует 1 день
        )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            url = data.get('link')
            print(f"   ✅ Загружено: {url}")
            return url
    
    print(f"   ❌ Ошибка: {response.text}")
    return None

def upload_to_0x0(filepath: str) -> str:
    """Загрузить файл на 0x0.st и получить публичный URL"""
    print(f"\n📤 Загрузка {filepath} на 0x0.st...")
    
    with open(filepath, 'rb') as f:
        response = requests.post(
            'https://0x0.st',
            files={'file': f}
        )
    
    if response.status_code == 200:
        url = response.text.strip()
        print(f"   ✅ Загружено: {url}")
        return url
    
    print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
    return None

def main():
    print("\n" + "="*60)
    print("🎬 GeeLark Video Upload & Instagram Reels Test")
    print("="*60)
    
    # Создаём клиент API
    client = GeeLarkAPI(bearer_token=BEARER_TOKEN, app_id=APP_ID)
    
    # Шаг 1: Проверяем статус телефона
    print(f"\n📱 Шаг 1: Проверка статуса телефона {PHONE_ID}...")
    status_result = client.get_phone_status([PHONE_ID])
    
    if status_result.get('success'):
        items = status_result.get('data', {}).get('items', [])
        if items:
            phone = items[0]
            status = phone.get('status')
            if status == 1:
                print(f"   ✅ Телефон запущен")
            else:
                print(f"   ⚠️ Телефон остановлен, запускаем...")
                start_result = client.start_phones([PHONE_ID])
                if start_result.get('success'):
                    print(f"   ✅ Команда запуска отправлена")
                    print(f"   ⏳ Ждём 30 секунд для загрузки...")
                    time.sleep(30)
                else:
                    print(f"   ❌ Ошибка запуска: {start_result}")
                    return
    else:
        print(f"   ❌ Ошибка: {status_result}")
        return
    
    # Шаг 2: Загружаем видео на публичный хостинг
    video_path = "/home/user/webapp/test_video.mp4"
    
    # Проверяем размер файла
    file_size = os.path.getsize(video_path)
    print(f"\n📁 Размер видео: {file_size / 1024 / 1024:.1f} MB")
    
    # file.io имеет лимит 2GB, но может быть медленным
    # 0x0.st имеет лимит 512MB
    
    if file_size > 500 * 1024 * 1024:  # > 500MB
        print("   ⚠️ Файл слишком большой, нужен другой хостинг")
        return
    
    print("\n📤 Шаг 2: Загрузка видео на публичный хостинг...")
    
    # Пробуем file.io (лучше для больших файлов)
    video_url = upload_to_fileio(video_path)
    
    if not video_url:
        print("   Пробуем 0x0.st...")
        video_url = upload_to_0x0(video_path)
    
    if not video_url:
        print("   ❌ Не удалось загрузить видео на хостинг")
        return
    
    # Шаг 3: Загружаем видео на телефон
    print(f"\n📲 Шаг 3: Загрузка видео на телефон...")
    print(f"   URL: {video_url}")
    
    upload_result = client.upload_file(PHONE_ID, video_url)
    
    if upload_result.get('success'):
        print(f"   ✅ Задача загрузки создана")
        
        # Получаем taskId если есть
        task_id = upload_result.get('data', {}).get('taskId')
        if task_id:
            print(f"   Task ID: {task_id}")
            
            # Ждём завершения загрузки
            print(f"\n⏳ Ожидание загрузки на телефон...")
            
            for i in range(30):  # максимум 5 минут
                time.sleep(10)
                
                task_result = client.query_task(task_id)
                if task_result.get('success') and task_result.get('task'):
                    task = task_result['task']
                    status = task.get('status')
                    status_name = TASK_STATUS.get(status, 'unknown')
                    
                    print(f"   [{i+1}/30] Статус: {status_name}")
                    
                    if status == 3:  # completed
                        print(f"   ✅ Видео загружено на телефон!")
                        break
                    elif status == 4:  # failed
                        fail_code = task.get('failCode')
                        fail_desc = TASK_FAILURE_CODES.get(fail_code, task.get('failDesc', 'Unknown'))
                        print(f"   ❌ Ошибка загрузки: {fail_desc}")
                        return
                    elif status == 7:  # cancelled
                        print(f"   ❌ Загрузка отменена")
                        return
            else:
                print(f"   ⚠️ Таймаут ожидания загрузки")
        else:
            print(f"   ⚠️ Нет taskId, возможно загрузка синхронная")
            print(f"   Ждём 30 секунд...")
            time.sleep(30)
    else:
        print(f"   ❌ Ошибка: {upload_result.get('msg')}")
        return
    
    # Шаг 4: Публикуем Reels
    print(f"\n📸 Шаг 4: Публикация Instagram Reels...")
    
    description = "Test Reels from GeeLark API 🎬\n\n#test #reels #instagram #automation"
    
    reels_result = client.publish_instagram_reels(
        phone_id=PHONE_ID,
        video_urls=[video_url],
        description=description
    )
    
    if reels_result.get('success'):
        task_id = reels_result.get('data', {}).get('taskId')
        print(f"   ✅ Задача публикации создана")
        print(f"   Task ID: {task_id}")
        
        # Мониторим статус
        print(f"\n⏳ Мониторинг публикации...")
        
        for i in range(60):  # максимум 10 минут
            time.sleep(10)
            
            task_result = client.query_task(task_id)
            if task_result.get('success') and task_result.get('task'):
                task = task_result['task']
                status = task.get('status')
                status_name = TASK_STATUS.get(status, 'unknown')
                
                print(f"   [{i+1}/60] Статус: {status_name}")
                
                if status == 3:  # completed
                    share_link = task.get('shareLink')
                    print(f"\n   🎉 УСПЕХ! Reels опубликован!")
                    if share_link:
                        print(f"   🔗 Ссылка: {share_link}")
                    break
                elif status == 4:  # failed
                    fail_code = task.get('failCode')
                    fail_desc = TASK_FAILURE_CODES.get(fail_code, task.get('failDesc', 'Unknown'))
                    print(f"\n   ❌ Ошибка публикации: {fail_desc} (код: {fail_code})")
                    break
                elif status == 7:  # cancelled
                    print(f"\n   ❌ Публикация отменена")
                    break
        else:
            print(f"\n   ⚠️ Таймаут ожидания публикации")
    else:
        print(f"   ❌ Ошибка: {reels_result.get('msg')}")
    
    print("\n" + "="*60)
    print("✅ Тест завершён")
    print("="*60)

if __name__ == "__main__":
    main()
