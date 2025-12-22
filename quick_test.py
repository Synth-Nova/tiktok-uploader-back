#!/usr/bin/env python3
"""Быстрый тест с маленьким видео"""

import os
import sys
import time
import requests

sys.path.insert(0, '/home/user/webapp/instagram-reels-bot/src')
from integrations.geelark_api import GeeLarkAPI, TASK_STATUS, TASK_FAILURE_CODES

APP_ID = "2FC9X9O4798WG301A0811VYO"
BEARER_TOKEN = "PLL2GCYJ0HYW6ZOL74UJBXSXFMG3JT"
PHONE_ID = "597099542109749349"

def upload_video(filepath: str) -> str:
    """Загрузить видео на catbox"""
    print(f"📤 Загрузка {os.path.basename(filepath)} ({os.path.getsize(filepath)/1024/1024:.1f}MB)...")
    
    try:
        with open(filepath, 'rb') as f:
            resp = requests.post(
                'https://catbox.moe/user/api.php',
                files={'fileToUpload': f},
                data={'reqtype': 'fileupload'},
                timeout=120
            )
        
        if resp.status_code == 200 and resp.text.startswith('http'):
            print(f"   ✅ {resp.text.strip()}")
            return resp.text.strip()
    except Exception as e:
        print(f"   ❌ {e}")
    
    # Fallback: litterbox
    try:
        print("   Пробуем litterbox...")
        with open(filepath, 'rb') as f:
            resp = requests.post(
                'https://litterbox.catbox.moe/resources/internals/api.php',
                files={'fileToUpload': f},
                data={'reqtype': 'fileupload', 'time': '1h'},
                timeout=120
            )
        if resp.status_code == 200 and resp.text.startswith('http'):
            print(f"   ✅ {resp.text.strip()}")
            return resp.text.strip()
    except Exception as e:
        print(f"   ❌ {e}")
    
    return None

def main():
    print("="*50)
    print("🎬 Quick GeeLark Test")
    print("="*50)
    
    client = GeeLarkAPI(bearer_token=BEARER_TOKEN, app_id=APP_ID)
    
    # 1. Проверка телефона
    print(f"\n📱 Телефон {PHONE_ID}...")
    status = client.get_phone_status([PHONE_ID])
    
    if status.get('success'):
        items = status.get('data', {}).get('items', [])
        if items:
            running = items[0].get('status') == 1
            print(f"   {'🟢 Работает' if running else '⚪ Остановлен'}")
            
            if not running:
                print("   Запускаем...")
                client.start_phones([PHONE_ID])
                time.sleep(30)
    
    # 2. Загрузка видео на хостинг
    video_url = upload_video("/home/user/webapp/small_test.mp4")
    if not video_url:
        print("❌ Не удалось загрузить видео")
        return
    
    # 3. Загрузка на телефон
    print(f"\n📲 Отправка на телефон...")
    upload = client.upload_file(PHONE_ID, video_url)
    print(f"   Результат: {upload.get('success')} - {upload.get('msg', 'OK')}")
    
    if upload.get('success'):
        task_id = upload.get('data', {}).get('taskId')
        if task_id:
            print(f"   Task: {task_id}")
            # Ждём загрузки
            for i in range(10):
                time.sleep(10)
                r = client.query_task(task_id)
                if r.get('task'):
                    s = r['task'].get('status')
                    print(f"   [{i+1}] {TASK_STATUS.get(s, s)}")
                    if s in [3, 4, 7]:
                        break
        else:
            print("   Ждём 30 сек...")
            time.sleep(30)
    
    # 4. Публикация Reels
    print(f"\n📸 Публикация Reels...")
    
    reels = client.publish_instagram_reels(
        phone_id=PHONE_ID,
        video_urls=[video_url],
        description="Test 🎬 #test #reels"
    )
    
    print(f"   Результат: {reels.get('success')} - {reels.get('msg', 'OK')}")
    
    if reels.get('success'):
        task_id = reels.get('data', {}).get('taskId')
        print(f"   Task: {task_id}")
        
        print("\n⏳ Мониторинг...")
        for i in range(30):
            time.sleep(10)
            r = client.query_task(task_id)
            if r.get('task'):
                t = r['task']
                s = t.get('status')
                print(f"   [{i+1}] {TASK_STATUS.get(s, s)}")
                
                if s == 3:
                    print(f"\n🎉 УСПЕХ! Link: {t.get('shareLink', 'N/A')}")
                    break
                elif s == 4:
                    code = t.get('failCode')
                    print(f"\n❌ Ошибка: {TASK_FAILURE_CODES.get(code, t.get('failDesc'))} ({code})")
                    break
                elif s == 7:
                    print("\n❌ Отменено")
                    break
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
