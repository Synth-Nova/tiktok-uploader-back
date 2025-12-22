# 🚀 Быстрый старт для разработки мобильного приложения 5scene

**Для Claude Opus 4.5** | Дата: 2025-12-22

---

## 🔐 Главные учетные данные

### Development Server (работай здесь!)
```
URL: https://upl.synthnova.me/
Dashboard: https://upl.synthnova.me/dashboard
Логин: admin
Пароль: rewfdsvcx5

SSH: ssh root@217.198.12.144
```

### Production (⚠️ НЕ ТРОГАТЬ!)
```
URL: http://89.23.100.188:3000/dashboard
Логин: admin
Пароль: admin1
```

---

## 🌐 API для мобильного приложения

### 1. Основной API (TikTok/YouTube)
```
https://upl.synthnova.me/api
```
**Что умеет:**
- Загрузка видео в TikTok/YouTube
- История загрузок
- Управление аккаунтами
- Статистика

### 2. Video Editor API
```
https://upl.synthnova.me/video-editor-api
```
**Что умеет:**
- Smart Video Montage (склейка видео)
- Voice & Subtitles (озвучка + субтитры)
- Avatar Generator (создание аватаров)

### 3. Video Uniquifier API
```
https://upl.synthnova.me/uniquifier-api
```
**Что умеет:**
- 12 методов уникализации видео
- 3 пресета модификаций
- ⚠️ Требует ручного запуска на сервере!

---

## 🔑 API Keys для внешних сервисов

```bash
# ElevenLabs (Voice Generation)
ELEVENLABS_API_KEY=sk_9537f51db5a1bbf57f6ef774e4fe1c23de43617d0123a177

# HeyGen (Avatar Generation)
HEYGEN_API_KEY=sk_V2_hgu_kqlUGXHp4ZH_9KpXEW7bSJtfoy4tXvhvcgm1no0xFPtN
```

---

## 📂 GitHub

```
Основной репозиторий:
https://github.com/Synth-Nova/tiktok-uploader-back

Backend:
https://github.com/Synth-Nova/influence1

Frontend:
https://github.com/Synth-Nova/influence2
```

---

## 🎯 Что нужно сделать?

1. **Создать мобильное приложение для 5scene**
2. **Интегрировать с существующими API** (см. выше)
3. **Использовать те же credentials** для авторизации

---

## 📱 Примеры использования API

### Авторизация (JWT)
```javascript
// POST https://upl.synthnova.me/api/login
{
  "username": "admin",
  "password": "rewfdsvcx5"
}
// Ответ: { "token": "jwt_token_here" }
```

### Загрузка видео
```javascript
// POST https://upl.synthnova.me/api/upload
// Headers: { "Authorization": "Bearer jwt_token" }
// FormData: { video: file, caption: "text", ... }
```

### Генерация голоса (Video Editor)
```javascript
// POST https://upl.synthnova.me/video-editor-api/api/voice-subtitles/generate-voice
{
  "text": "Текст для озвучки",
  "voice_id": "optional"
}
```

### Уникализация видео (Uniquifier)
```javascript
// POST https://upl.synthnova.me/uniquifier-api/api/uniquify
{
  "video_url": "url",
  "methods": ["speed", "brightness", "mirror"]
}
```

---

## 📝 Важные документы (читай обязательно!)

В `/home/user/webapp/` находятся:

1. **PROJECT_QUICK_START.md** - НАЧНИ С ЭТОГО!
2. **CREDENTIALS_CHEATSHEET.md** - Все пароли
3. **VIDEO_EDITOR_DOCS.md** - Документация Video Editor
4. **HANDOFF_TO_MOBILE_DEV.md** - Полная информация для передачи

---

## 🔄 Git Workflow (ОБЯЗАТЕЛЬНО!)

После ЛЮБОГО изменения кода:

```bash
cd /home/user/webapp

# 1. Commit
git add .
git commit -m "feat: описание"

# 2. Sync с remote
git fetch origin main
git rebase origin/main

# 3. Squash коммитов
git reset --soft HEAD~N  # N = кол-во коммитов
git commit -m "comprehensive message"

# 4. Push
git push -f origin main

# 5. Создать PR и ДАТЬ ССЫЛКУ пользователю!
```

---

## 🧪 Быстрая проверка

```bash
# Проверка Frontend
curl -I https://upl.synthnova.me/

# Проверка API
curl https://upl.synthnova.me/api/health

# Проверка Video Editor
curl https://upl.synthnova.me/video-editor-api/

# SSH на сервер
ssh root@217.198.12.144

# Статус сервисов
pm2 status
```

---

## ⚠️ Критические правила

1. ❌ **НЕ ТРОГАЙ Production** (`89.23.100.188`)
2. ✅ **Работай ТОЛЬКО на Fork** (`217.198.12.144`)
3. ✅ **Всегда делай commit после изменений**
4. ✅ **Всегда создавай PR и давай ссылку**
5. ✅ **Делай бэкап перед большими изменениями**
6. ✅ **Используй HTTPS Nginx прокси, не прямые порты!**

---

## 💡 Полезные команды

```bash
# SSH доступ
ssh root@217.198.12.144

# PM2 управление
pm2 status
pm2 logs video-editor-api
pm2 restart video-editor-api

# Nginx
systemctl status nginx
nginx -t
systemctl reload nginx

# Бэкап
ssh root@217.198.12.144 '/root/backup-all.sh'
```

---

## 🆘 Если что-то сломалось

1. Читай логи: `pm2 logs --lines 100`
2. Проверяй Nginx: `nginx -t`
3. Смотри бэкапы: `/root/project-backups/`
4. Изучай документацию: `PROJECT_QUICK_START.md`

---

**Удачи в разработке! 🚀**

_Для полной информации читай `HANDOFF_TO_MOBILE_DEV.md`_
