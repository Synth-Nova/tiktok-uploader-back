# 🎬 VIDEO EDITOR MODULE - Complete Documentation

**Дата создания:** 2025-12-22  
**Статус:** ✅ Deployed and Running  
**URL:** https://upl.synthnova.me/video-editor  
**API:** http://217.198.12.144:8081 (Nginx proxy: /video-editor-api)

---

## 📋 ОБЗОР

Video Editor - это модуль для монтажа видео с 3 мощными подмодулями:

1. **📹 Smart Video Montage** - Автоматический монтаж с перемешиванием шотов
2. **🎙️ Voice & Subtitles Generator** - Генерация голоса и субтитров
3. **👤 Avatar Generator** - Создание talking head видео

---

## 🏗️ АРХИТЕКТУРА

```
Video Editor Module
├── Backend (Python Flask API - порт 8081)
│   ├── app.py
│   ├── api/
│   │   ├── montage.py (Smart Video Montage)
│   │   ├── voice_subtitles.py (Voice & Subtitles)
│   │   └── avatar.py (Avatar Generator)
│   ├── requirements.txt
│   └── .env (API keys)
│
└── Frontend (React TypeScript)
    ├── pages/VideoEditor.tsx
    ├── styles/VideoEditor.scss
    └── API integration
```

---

## 🚀 DEPLOYMENT

### Backend (Python Flask API)

**Локация:** `/opt/video-editor`  
**Python:** Python 3.12 + virtualenv  
**Порт:** 8081  
**PM2 Process:** `video-editor-api`

**Запуск:**
```bash
cd /opt/video-editor
pm2 start ecosystem.config.js
pm2 status
```

**Логи:**
```bash
pm2 logs video-editor-api
pm2 logs video-editor-api --lines 50
```

**Рестарт:**
```bash
pm2 restart video-editor-api
```

### Frontend (React)

**Локация:** `/opt/influence-frontend/build`  
**URL:** https://upl.synthnova.me/video-editor  
**Nginx Config:** `/etc/nginx/sites-available/influence`

**Rebuild и Deploy:**
```bash
cd /home/user/webapp/my-tiktok-uploader/frontend
npm run build
tar -czf /tmp/frontend-new.tar.gz build/
scp /tmp/frontend-new.tar.gz root@217.198.12.144:/tmp/
ssh root@217.198.12.144
cd /tmp
rm -rf /opt/influence-frontend/build/*
tar -xzf frontend-new.tar.gz -C /opt/influence-frontend/
systemctl reload nginx
```

---

## 📹 ПОДМОДУЛЬ 1: Smart Video Montage

### Функционал

- Загрузка 8+ видео шотов
- Фиксированные позиции: Hook (первый) и CTA (последний)
- Случайное перемешивание средних шотов
- Генерация множества вариантов монтажа
- Наложение аудио дорожки
- Наложение аватара с прозрачным фоном
- Опциональная генерация субтитров

### API Endpoint

**POST** `/api/montage/create`

**Request (multipart/form-data):**
```
shots[]: File[] (минимум 3 файла)
audio: File (опционально)
avatar: File (опционально)
shuffle_count: number (количество вариантов, по умолчанию 1)
add_subtitles: boolean
```

**Response:**
```json
{
  "success": true,
  "project_id": "20251222_070530",
  "variants_created": 3,
  "outputs": [
    {
      "variant": 0,
      "filename": "montage_20251222_070530_v00.mp4",
      "url": "/api/montage/download/montage_20251222_070530_v00.mp4",
      "shots_order": ["shot_00_hook.mp4", "shot_02_middle.mp4", "shot_01_middle.mp4", "shot_03_cta.mp4"]
    }
  ],
  "hook": "shot_00_hook.mp4",
  "cta": "shot_03_cta.mp4",
  "middle_shots_count": 2
}
```

### Технологии

- **FFmpeg** - монтаж видео
- **Python moviepy** - обработка видео
- **Random shuffling** - перемешивание шотов

---

## 🎙️ ПОДМОДУЛЬ 2: Voice & Subtitles Generator

### Функционал

- Генерация голоса из текста (ElevenLabs API)
- Генерация субтитров из аудио (Whisper)
- Поддержка множества языков
- Выбор голосов (male/female)
- Скачивание готовых файлов

### API Endpoints

#### 1. Генерация голоса

**POST** `/api/voice-subtitles/generate-voice`

**Request:**
```json
{
  "text": "Текст для озвучки",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "language": "en",
  "model_id": "eleven_multilingual_v2"
}
```

**Response:**
```json
{
  "success": true,
  "filename": "voice_20251222_070530.mp3",
  "url": "/api/voice-subtitles/download/voice_20251222_070530.mp3",
  "text_length": 50,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "language": "en"
}
```

#### 2. Генерация субтитров

**POST** `/api/voice-subtitles/generate-subtitles`

**Request (multipart/form-data):**
```
audio: File
language: string (auto, en, ru, etc.)
format: string (srt, vtt, json)
```

**Response:**
```json
{
  "success": true,
  "filename": "subtitles_20251222_070530.srt",
  "url": "/api/voice-subtitles/download/subtitles_20251222_070530.srt",
  "format": "srt",
  "content": "1\n00:00:00,000 --> 00:00:05,000\nПример субтитров",
  "method": "whisper-local"
}
```

#### 3. Список голосов

**GET** `/api/voice-subtitles/list-voices`

**Response:**
```json
{
  "success": true,
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "category": "premade",
      "labels": { "gender": "female", "age": "young" }
    }
  ],
  "count": 50
}
```

### API Keys

**ElevenLabs API:**  
`sk_9537f51db5a1bbf57f6ef774e4fe1c23de43617d0123a177`

**Доступные голоса:**
- Rachel (Female) - `21m00Tcm4TlvDq8ikWAM`
- Domi (Female) - `AZnzlk1XvdvUeBnXmlld`
- Bella (Female) - `EXAVITQu4vr4xnSDxMaL`
- Antoni (Male) - `ErXwobaYiN019PkySvjV`
- Arnold (Male) - `VR6AewLTigWG4xSOukaG`

---

## 👤 ПОДМОДУЛЬ 3: Avatar Generator (HeyGen)

### Функционал

- Создание talking head видео
- Настраиваемые аватары
- Множество голосов
- Асинхронная генерация
- Проверка статуса
- Скачивание готового видео

### API Endpoints

#### 1. Создать аватар

**POST** `/api/avatar/create`

**Request:**
```json
{
  "text": "Текст, который скажет аватар",
  "avatar_id": "default",
  "voice_id": "default",
  "language": "en",
  "background": "#FFFFFF"
}
```

**Response:**
```json
{
  "success": true,
  "video_id": "abc123xyz",
  "status": "processing",
  "message": "Video generation started.",
  "check_url": "/api/avatar/status/abc123xyz"
}
```

#### 2. Проверить статус

**GET** `/api/avatar/status/<video_id>`

**Response:**
```json
{
  "success": true,
  "video_id": "abc123xyz",
  "status": "completed",
  "video_url": "https://heygen.com/video/abc123xyz.mp4",
  "download_url": "/api/avatar/download/abc123xyz"
}
```

#### 3. Список аватаров

**GET** `/api/avatar/list-avatars`

**Response:**
```json
{
  "success": true,
  "avatars": [
    {
      "avatar_id": "josh_lite3_20230714",
      "avatar_name": "Josh",
      "gender": "male",
      "preview_image": "https://...",
      "preview_video": "https://..."
    }
  ],
  "count": 20
}
```

### API Key

**HeyGen API:**  
`sk_V2_hgu_kqlUGXHp4ZH_9KpXEW7bSJtfoy4tXvhvcgm1no0xFPtN`

---

## 🌐 NGINX CONFIGURATION

**Файл:** `/etc/nginx/sites-available/influence`

```nginx
# Video Editor API proxy (порт 8081)
location /video-editor-api {
    rewrite ^/video-editor-api/(.*) /$1 break;
    proxy_pass http://127.0.0.1:8081;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 500M;
    proxy_connect_timeout 1800s;
    proxy_send_timeout 1800s;
    proxy_read_timeout 1800s;
}
```

**Перезагрузка:**
```bash
nginx -t
systemctl reload nginx
```

---

## 📊 PM2 MANAGEMENT

**Проверка статуса:**
```bash
pm2 status
pm2 info video-editor-api
```

**Логи:**
```bash
pm2 logs video-editor-api
pm2 logs video-editor-api --lines 100
pm2 logs video-editor-api --err
```

**Управление:**
```bash
pm2 restart video-editor-api
pm2 stop video-editor-api
pm2 delete video-editor-api
```

**Автозапуск:**
```bash
pm2 startup
pm2 save
```

---

## 🔧 TROUBLESHOOTING

### API не отвечает

```bash
# Проверка статуса
pm2 status
pm2 logs video-editor-api --lines 50

# Проверка порта
curl http://localhost:8081/
netstat -tulpn | grep 8081

# Рестарт
pm2 restart video-editor-api
```

### Frontend не обновился

```bash
# Очистить кеш браузера
Ctrl + Shift + R (или Cmd + Shift + R)

# Проверить файлы
ls -la /opt/influence-frontend/build/

# Перезагрузить Nginx
systemctl reload nginx
```

### Ошибка генерации видео

```bash
# Проверить FFmpeg
ffmpeg -version

# Проверить права доступа
ls -la /opt/video-editor/uploads/
ls -la /opt/video-editor/outputs/

# Исправить права
chown -R www-data:www-data /opt/video-editor/uploads
chown -R www-data:www-data /opt/video-editor/outputs
```

---

## 📚 ДОКУМЕНТАЦИЯ API

### Base URL

**Production:** `https://upl.synthnova.me/video-editor-api`  
**Development:** `http://217.198.12.144:8081`

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "timestamp": "2025-12-22T07:05:55.794105"
}
```

### API Keys Check

**GET** `/api/check-keys`

```json
{
  "elevenlabs": "configured",
  "heygen": "configured"
}
```

---

## 🔐 CREDENTIALS

### API Keys

**ElevenLabs:**  
`sk_9537f51db5a1bbf57f6ef774e4fe1c23de43617d0123a177`

**HeyGen:**  
`sk_V2_hgu_kqlUGXHp4ZH_9KpXEW7bSJtfoy4tXvhvcgm1no0xFPtN`

### Frontend Access

**URL:** https://upl.synthnova.me/video-editor  
**Login:** admin  
**Password:** rewfdsvcx5

---

## 📈 СТАТУС DEPLOYMENT

✅ **Backend API** - Running on port 8081  
✅ **Frontend UI** - Deployed at /video-editor  
✅ **Nginx Proxy** - Configured for /video-editor-api  
✅ **PM2 Process** - video-editor-api (online)  
✅ **Submodules** - All 3 functional

---

## 🚀 QUICK START

### Использование

1. Откройте https://upl.synthnova.me/video-editor
2. Войдите (admin / rewfdsvcx5)
3. Выберите подмодуль в табах
4. Загрузите файлы / введите текст
5. Нажмите "Создать" / "Сгенерировать"
6. Скачайте готовый результат

### API Testing

```bash
# Check API
curl http://217.198.12.144:8081/

# Test Voice Generation
curl -X POST http://217.198.12.144:8081/api/voice-subtitles/generate-voice \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice_id": "21m00Tcm4TlvDq8ikWAM", "language": "en"}'

# List Voices
curl http://217.198.12.144:8081/api/voice-subtitles/list-voices
```

---

## 📝 CHANGELOG

### v1.0.0 - 2025-12-22

✨ **Initial Release**

- Подмодуль 1: Smart Video Montage
- Подмодуль 2: Voice & Subtitles Generator
- Подмодуль 3: Avatar Generator (HeyGen)
- React Frontend UI
- Python Flask Backend API
- Nginx proxy configuration
- PM2 process management
- Full deployment on production server

---

## 🔗 LINKS

- **Frontend:** https://upl.synthnova.me/video-editor
- **API:** http://217.198.12.144:8081
- **GitHub (Main):** https://github.com/Synth-Nova/tiktok-uploader-back
- **GitHub (Frontend):** https://github.com/Synth-Nova/influence2
- **PM2 Dashboard:** `pm2 monit`

---

## 💡 NOTES

- **FFmpeg** должен быть установлен на сервере для монтажа видео
- **Whisper** (опционально) для генерации субтитров
- **ElevenLabs API** имеет лимиты на генерацию голоса
- **HeyGen API** - асинхронная генерация (проверка статуса каждые 30 сек)
- **Максимальный размер файла:** 500 MB (настроено в Nginx)

---

**Дата обновления:** 2025-12-22  
**Версия:** 1.0.0  
**Статус:** ✅ Production Ready
