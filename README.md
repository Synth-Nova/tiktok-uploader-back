# 🚀 TikTok/Instagram Multi-Platform Video Automation

**Форк проект для разработки и тестирования (Timeweb Cloud ID 6186087)**

Комплексная система автоматизации загрузки видео на TikTok, YouTube и Instagram с функциями уникализации контента и управления облачными телефонами.

---

## 🎯 О проекте

Этот репозиторий является **форком для разработки** основного проекта (ID 5788751). Здесь мы тестируем новые функции перед их внедрением в production.

### Ключевые возможности:
- ✅ **TikTok Uploader** - автоматическая загрузка видео через Selenium
- ✅ **YouTube Uploader** - массовая публикация на YouTube
- ✅ **Instagram Reels Bot** - автоматизация публикаций через облачные телефоны
- 🎬 **Video Uniquifier v2.0** - создание уникальных версий видео (12 методов модификации)
- 🌈 **Background Uniquifier** - генерация 96 уникальных фонов (12 языков × 8 спикеров)
- ☁️ **Cloud Phone Integration** - GeeLark и DuoPlus API

---

## 🏗️ Архитектура

### Основной проект (ID 5788751) - PRODUCTION
```
http://89.23.100.188:3000
├── Backend: influence1 (https://github.com/Synth-Nova/influence1)
└── Frontend: influence2 (https://github.com/Synth-Nova/influence2)
```
**⚠️ Production environment - не трогать без согласования!**

### Форк проект (ID 6186087) - DEVELOPMENT ← **ВЫ ЗДЕСЬ**
```
https://217.198.12.144/
├── Wrapper: tiktok-uploader-back (https://github.com/Synth-Nova/tiktok-uploader-back)
│   ├── Субмодули: influence1 + influence2
│   ├── Instagram Reels Bot (Python)
│   ├── Video Uniquifier v2.0 (Python Flask)
│   └── Полная документация
```
**✅ Development/Testing environment - здесь можно экспериментировать!**

---

## 🔐 Доступы

### Форк проект (Development)
- **URL:** https://217.198.12.144/
- **Login:** `admin`
- **Password:** `rewfdsvcx5`

### API Endpoints
- **TikTok API:** http://217.198.12.144:3000
- **YouTube API:** http://72.56.76.237:3000
- **Uniquifier API:** http://217.198.12.144:8080 ⚠️ *требует запуска*

> 📝 Полные credentials в файле [CREDENTIALS_CHEATSHEET.md](./CREDENTIALS_CHEATSHEET.md)

---

## 🎬 Video Uniquifier

### Что это?
Python Flask API для создания уникальных версий видео с разными хэшами для обхода детектирования дубликатов.

### 12 методов модификации:
1. 📐 **Crop** - обрезка до 5%
2. 💡 **Brightness** - яркость до 10%
3. 🎨 **Saturation** - насыщенность до 10%
4. 🌈 **Hue Shift** - сдвиг оттенка до 10°
5. ⚡ **Speed** - скорость до 5%
6. 🎵 **Pitch** - высота звука до 2 полутонов
7. 📡 **Noise** - шум до 0.01
8. 🔄 **Rotation** - вращение до 2°
9. ✂️ **Frame Trimming** - обрезка кадров до 300ms
10. 🎨 **Color Shift** - сдвиг цвета до 5%
11. 🔆 **Gamma** - гамма до 5%
12. 💧 **Watermark** - прозрачность до 2%

### 3 пресета:
- **Minimal:** Легкие изменения (5-10%)
- **Balanced:** Средние изменения (30-50%)
- **Aggressive:** Максимальные изменения (80-100%)

### Использование:
```bash
cd instagram-reels-bot
python3 run_uniquifier.py web 8080
```

Затем откройте: https://217.198.12.144/uniquifier

---

## 🤖 Instagram Reels Bot

### Возможности:
- ✅ Автоматизация публикаций в Instagram Reels
- ✅ Интеграция с GeeLark Cloud Phone API
- ✅ Интеграция с DuoPlus Cloud Phone API (27+ endpoints)
- ✅ Background Uniquifier (96 версий фонов)
- ✅ Система управления аккаунтами
- ✅ База данных SQLite для трекинга

### Модули:
```
instagram-reels-bot/
├── src/integrations/
│   └── geelark_api.py       # GeeLark API клиент
├── src/modules/
│   ├── auto_login.py        # Автологин
│   ├── email_parser.py      # Парсер email
│   └── reels_uploader.py    # Загрузчик Reels
├── src/tools/
│   ├── video_uniquifier.py  # Ядро обработки видео
│   └── uniquifier_web.py    # Flask веб-сервер
├── background_uniquifier.py # Генератор фонов
└── run_uniquifier.py        # Главный скрипт
```

---

## 📚 Документация

### Быстрый старт:
- 🚀 **[PROJECT_QUICK_START.md](./PROJECT_QUICK_START.md)** - Полная справка для быстрого старта (читать первым!)
- 🔐 **[CREDENTIALS_CHEATSHEET.md](./CREDENTIALS_CHEATSHEET.md)** - Шпаргалка с паролями

### Техническая документация:
- 📖 **[PROJECT_REPOSITORIES.md](./PROJECT_REPOSITORIES.md)** - Структура GitHub репозиториев
- 🎬 **[UNIQUIFIER_INTEGRATION.md](./UNIQUIFIER_INTEGRATION.md)** - План интеграции Uniquifier (380+ строк)
- 📺 **[TIKTOK_UPLOADER_DOCS.md](./TIKTOK_UPLOADER_DOCS.md)** - TikTok Uploader документация
- 📊 **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Обзор и статус проекта
- 🔧 **[MODULE_INTEGRATION_PLAN.md](./MODULE_INTEGRATION_PLAN.md)** - План интеграции модулей
- 🏗️ **[TECHNICAL_STRUCTURE.md](./TECHNICAL_STRUCTURE.md)** - Техническая структура
- 📐 **[ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)** - Архитектурные диаграммы

---

## 🚀 Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/Synth-Nova/tiktok-uploader-back.git
cd tiktok-uploader-back
```

### 2. Инициализировать субмодули
```bash
git submodule update --init --recursive
```

### 3. Установка зависимостей

#### Frontend (React)
```bash
cd my-tiktok-uploader/frontend
npm install
```

#### Backend (Node.js)
```bash
cd my-tiktok-uploader/backend
npm install
```

#### Instagram Reels Bot (Python)
```bash
cd instagram-reels-bot
pip install -r requirements.txt
```

### 4. Настройка Environment Variables

#### Frontend (.env.production)
```env
REACT_APP_API_URL=http://217.198.12.144:3000
YOUTUBE_API_BASE_URL=http://72.56.76.237:3000
REACT_APP_UNIQUIFIER_URL=http://217.198.12.144:8080
```

### 5. Запуск

#### Frontend
```bash
cd my-tiktok-uploader/frontend
npm start  # Development: http://localhost:3000
npm run build  # Production build
```

#### Backend
```bash
cd my-tiktok-uploader/backend
npm start  # Port 3000
```

#### Uniquifier API
```bash
cd instagram-reels-bot
python3 run_uniquifier.py web 8080
```

---

## 🛠️ Tech Stack

### Frontend
- **React** 18.x + TypeScript
- **React Router** для навигации
- **SCSS** для стилей
- **Axios** для API запросов

### Backend
- **Node.js** + Express
- **TypeScript**
- **Selenium WebDriver** для автоматизации браузера
- **Bull Queue** для управления очередями
- **Prisma ORM** для базы данных
- **Redis** для кеширования

### Instagram Bot
- **Python** 3.8+
- **Flask** для веб API
- **FFmpeg** для обработки видео
- **SQLite** для базы данных
- **Requests** для API интеграций

---

## 📊 Текущий статус

### ✅ Завершено:
- [x] Интеграция Video Uniquifier в React UI
- [x] Создание всей документации проекта
- [x] Instagram Reels Bot базовая функциональность
- [x] GeeLark API клиент
- [x] DuoPlus API клиент (27 endpoints)
- [x] Background Uniquifier (96 версий)
- [x] Git workflow настроен

### ⏳ В процессе:
- [ ] Развертывание Python Backend Uniquifier на Timeweb (порт 8080)
- [ ] Ребилд и deploy React Frontend с новыми изменениями
- [ ] Активация DuoPlus API ключа
- [ ] Отладка GeeLark RPA task

### 📅 Планируется:
- [ ] Миграция YouTube API на Timeweb Cloud
- [ ] JWT аутентификация
- [ ] Улучшение безопасности (env vars)
- [ ] Полная автоматизация Instagram Reels
- [ ] Интеграция AdsPower API

---

## 🔧 Развертывание на Timeweb Cloud

### 1. SSH на сервер
```bash
ssh user@217.198.12.144
```

### 2. Клонировать проект
```bash
cd /var/www
git clone https://github.com/Synth-Nova/tiktok-uploader-back.git
cd tiktok-uploader-back
git submodule update --init --recursive
```

### 3. Backend
```bash
cd my-tiktok-uploader/backend
npm install
pm2 start server.js --name "tiktok-backend"
```

### 4. Frontend
```bash
cd my-tiktok-uploader/frontend
npm install
npm run build
# Копировать build/ в /var/www/html
```

### 5. Uniquifier API
```bash
cd instagram-reels-bot
pip install -r requirements.txt
pm2 start "python3 run_uniquifier.py web 8080" --name "uniquifier"
```

### 6. Настройка Nginx
```nginx
server {
    listen 443 ssl;
    server_name 217.198.12.144;
    
    # Frontend
    location / {
        root /var/www/html;
        try_files $uri /index.html;
    }
    
    # TikTok API
    location /api {
        proxy_pass http://localhost:3000;
    }
    
    # Uniquifier API
    location /uniquifier {
        proxy_pass http://localhost:8080;
    }
}
```

---

## 🤝 Contributing

### Git Workflow:

1. **Создать feature ветку:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Внести изменения и коммитить:**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

3. **Синхронизация с main:**
   ```bash
   git fetch origin main
   git rebase origin/main
   ```

4. **Объединить коммиты (если несколько):**
   ```bash
   git reset --soft origin/main
   git commit -m "feat: Comprehensive feature description"
   ```

5. **Push и создание PR:**
   ```bash
   git push origin feature/new-feature
   # Создать PR на GitHub
   ```

### Правила:
- ✅ **МОЖНО** менять код в форк проекте (ID 6186087)
- ❌ **НЕЛЬЗЯ** трогать основной проект (ID 5788751) без согласования
- ✅ **ВСЕГДА** коммитить после каждого изменения
- ✅ **ВСЕГДА** создавать Pull Request
- ✅ **ВСЕГДА** синхронизироваться перед PR

---

## 👥 Команда

- **@Synth-Nova** - Владелец организации
- **@Christiangrandcrue** - Lead Developer

---

## 📄 Лицензия

Proprietary - All rights reserved

---

## 🔗 Полезные ссылки

### GitHub Repositories:
- **Main Repo:** https://github.com/Synth-Nova/tiktok-uploader-back
- **Backend:** https://github.com/Synth-Nova/influence1
- **Frontend:** https://github.com/Synth-Nova/influence2

### Production:
- **Main Project:** http://89.23.100.188:3000 (ID 5788751)
- **Fork Project:** https://217.198.12.144/ (ID 6186087)

### External APIs:
- **DuoPlus:** https://my.duoplus.net/
- **GeeLark:** https://www.geelark.com/

---

## 📞 Поддержка

Для вопросов и проблем:
1. Проверьте документацию: [PROJECT_QUICK_START.md](./PROJECT_QUICK_START.md)
2. Посмотрите [CREDENTIALS_CHEATSHEET.md](./CREDENTIALS_CHEATSHEET.md)
3. Создайте Issue на GitHub

---

**Последнее обновление:** 2025-12-22  
**Версия:** 1.0.0  
**Статус:** 🟢 Active Development

---

<p align="center">
  Made with ❤️ by Synth-Nova Team
</p>
