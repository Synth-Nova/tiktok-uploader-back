#!/usr/bin/env python3
"""
Тест загрузки видео на GeeLark - версия 2
Используем несколько хостингов для надёжности
"""

import os
import sys
import time
import requests

sys.path.insert(0, '/home/user/webapp/instagram-reels-bot/src')
from integrations.geelark_api import GeeLarkAPI, TASK_STATUS, TASK_FAILURE_CODES

# Учётные данные
APP_ID = "2FC9X9O4798WG301A0811VYO"
BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"
PHONE_ID = "597099542109749349"

def upload_to_litterbox(filepath: str) -> str:
    """Загрузить на litterbox.catbox.moe (1 час хранения, до 1GB)"""
    print(f"\n📤 Загрузка на litterbox.catbox.moe...")
    
    try:
        with open(filepath, 'rb') as f:
            response = requests.post(
                'https://litterbox.catbox.moe/resources/internals/api.php',
                files={'fileToUpload': f},
                data={'reqtype': 'fileupload', 'time': '1h'},
                timeout=300
            )
        
        if response.status_code == 200 and response.text.startswith('http'):
            url = response.text.strip()
            print(f"   ✅ Загружено: {url}")
            return url
        else:
            print(f"   ❌ Ответ: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return None

def upload_to_tmpfiles(filepath: str) -> str:
    """Загрузить на tmpfiles.org (до 100MB)"""
    print(f"\n📤 Загрузка на tmpfiles.org...")
    
    try:
        with open(filepath, 'rb') as f:
            response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files={'file': f},
                timeout=300
            )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                # Преобразуем URL для прямой загрузки
                url = data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                print(f"   ✅ Загружено: {url}")
                return url
        print(f"   ❌ Ответ: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return None

def upload_to_transfer_sh(filepath: str) -> str:
    """Загрузить на transfer.sh"""
    print(f"\n📤 Загрузка на transfer.sh...")
    
    try:
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            response = requests.put(
                f'https://transfer.sh/{filename}',
                data=f,
                timeout=300
            )
        
        if response.status_code == 200:
            url = response.text.strip()
            print(f"   ✅ Загружено: {url}")
            return url
        print(f"   ❌ Ответ: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return None

def main():
    print("\n" + "="*60)
    print("🎬 GeeLark Video Upload Test v2")
    print("="*60)
    
    client = GeeLarkAPI(bearer_token=BEARER_TOKEN, app_id=APP_ID)
    
    # Шаг 1: Проверяем телефон
    print(f"\n📱 Проверка телефона {PHONE_ID}...")
    status_result = client.get_phone_status([PHONE_ID])
    
    phone_running = False
    if status_result.get('success'):
        items = status_result.get('data', {}).get('items', [])
        if items:
            status = items[0].get('status')
            phone_running = (status == 1)
            print(f"   Статус: {'🟢 Запущен' if phone_running else '⚪ Остановлен'}")
            
            if not phone_running:
                print(f"   Запускаем телефон...")
                start = client.start_phones([PHONE_ID])
                print(f"   Результат: {start.get('msg', 'OK')}")
                print(f"   ⏳ Ждём 40 сек...")
                time.sleep(40)
                phone_running = True
    else:
        print(f"   ❌ Ошибка: {status_result}")
        return
    
    # Шаг 2: Загрузка видео
    video_path = "/home/user/webapp/test_video.mp4"
    file_size_mb = os.path.getsize(video_path) / 1024 / 1024
    print(f"\n📁 Видео: {video_path} ({file_size_mb:.1f} MB)")
    
    # Пробуем разные хостинги
    video_url = None
    
    # 1. litterbox (до 1GB)
    video_url = upload_to_litterbox(video_path)
    
    # 2. tmpfiles (до 100MB)
    if not video_url and file_size_mb < 100:
        video_url = upload_to_tmpfiles(video_path)
    
    # 3. transfer.sh
    if not video_url:
        video_url = upload_to_transfer_sh(video_path)
    
    if not video_url:
        print("\n❌ Не удалось загрузить видео ни на один хостинг")
        return
    
    print(f"\n✅ Видео доступно по URL: {video_url}")
    
    # Шаг 3: Загрузка на телефон
    print(f"\n📲 Загрузка видео на телефон GeeLark...")
    
    upload_result = client.upload_file(PHONE_ID, video_url)
    print(f"   Ответ API: {upload_result}")
    
    if upload_result.get('success'):
        print(f"   ✅ Команда отправлена")
        
        # Проверяем есть ли taskId
        task_id = upload_result.get('data', {}).get('taskId')
        
        if task_id:
            print(f"   Task ID: {task_id}")
            print(f"\n⏳ Ожидание загрузки...")
            
            for i in range(20):
                time.sleep(15)
                result = client.query_task(task_id)
                
                if result.get('success') and result.get('task'):
                    task = result['task']
                    status = task.get('status')
                    status_name = TASK_STATUS.get(status, f'unknown({status})')
                    print(f"   [{i+1}/20] {status_name}")
                    
                    if status == 3:
                        print(f"   ✅ Загрузка завершена!")
                        break
                    elif status in [4, 7]:
                        fail = TASK_FAILURE_CODES.get(task.get('failCode'), task.get('failDesc'))
                        print(f"   ❌ Ошибка: {fail}")
                        return
        else:
            # Нет taskId - возможно синхронная операция
            print(f"   ⚠️ Нет taskId, ждём 60 сек...")
            time.sleep(60)
    else:
        print(f"   ❌ Ошибка: {upload_result.get('msg')}")
        return
    
    # Шаг 4: Публикация Reels
    print(f"\n📸 Публикация Instagram Reels...")
    
    caption = "Test video from automation 🎬✨\n\n#test #reels #instagram"
    
    reels_result = client.publish_instagram_reels(
        phone_id=PHONE_ID,
        video_urls=[video_url],
        description=caption
    )
    
    print(f"   Ответ API: code={reels_result.get('code')}, msg={reels_result.get('msg')}")
    
    if reels_result.get('success'):
        task_id = reels_result.get('data', {}).get('taskId')
        print(f"   ✅ Задача создана: {task_id}")
        
        print(f"\n⏳ Мониторинг публикации (до 10 мин)...")
        
        for i in range(40):
            time.sleep(15)
            
            result = client.query_task(task_id)
            if result.get('success') and result.get('task'):
                task = result['task']
                status = task.get('status')
                status_name = TASK_STATUS.get(status, f'unknown({status})')
                
                print(f"   [{i+1}/40] {status_name}")
                
                if status == 3:
                    link = task.get('shareLink', 'нет ссылки')
                    print(f"\n🎉 УСПЕХ! Reels опубликован!")
                    print(f"🔗 Ссылка: {link}")
                    break
                elif status == 4:
                    code = task.get('failCode')
                    desc = TASK_FAILURE_CODES.get(code, task.get('failDesc', 'Unknown'))
                    print(f"\n❌ Ошибка: {desc} (код {code})")
                    break
                elif status == 7:
                    print(f"\n❌ Отменено")
                    break
        else:
            print(f"\n⚠️ Таймаут")
    else:
        print(f"   ❌ Ошибка: {reels_result}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
