# 🔧 Module Integration Plan - Influence Dev Project

**Дата:** 2025-12-22  
**Timeweb Cloud:** ID 6186087 (Influence Dev)  
**Цель:** Встроить новый модуль в систему

---

## 📦 Текущие модули проекта

### 1️⃣ Instagram Reels Bot (Python)
- **Location:** `/home/user/webapp/instagram-reels-bot/`
- **Purpose:** Автоматизация публикации Instagram Reels
- **Stack:** Python, GeeLark/DuoPlus API, Cloud Phones
- **Status:** 🟡 In Development (RPA debugging needed)

### 2️⃣ TikTok Uploader (TypeScript)
- **Location:** `/home/user/webapp/my-tiktok-uploader/backend/`
- **Repository:** `https://github.com/Synth-Nova/influence1`
- **Purpose:** Автоматизация загрузки видео в TikTok
- **Stack:** TypeScript, Node.js, Selenium WebDriver, Bull Queue
- **Server:** `http://217.198.12.144:3000` (Timeweb Cloud)
- **Status:** ✅ Production

### 3️⃣ YouTube Uploader (External)
- **Server:** `http://72.56.76.237:3000` (Old Server)
- **Purpose:** Автоматизация загрузки видео в YouTube
- **Stack:** Selenium WebDriver
- **Status:** ✅ Working (needs migration to Timeweb)

### 4️⃣ React Frontend (TypeScript)
- **Location:** `/home/user/webapp/my-tiktok-uploader/frontend/`
- **Repository:** `https://github.com/Synth-Nova/influence2`
- **Purpose:** UI для TikTok/YouTube uploaders
- **Stack:** React, TypeScript, SCSS
- **Status:** ✅ Production

---

## 🎯 Новый модуль (для встраивания)

**Требуется от пользователя:**
- ❓ Какой модуль нужно встроить?
- ❓ Какая функциональность должна быть добавлена?
- ❓ С какими существующими модулями он должен интегрироваться?

### Возможные варианты интеграции:

#### A) Video Processing Module
**Цель:** Интеграция Video Uniquifier с TikTok/YouTube uploaders
- Добавить обработку видео перед загрузкой
- Создать API endpoint в backend для uniquification
- Вызывать Python скрипты из Node.js backend

#### B) Instagram Cloud Phone Module
**Цель:** Расширение Instagram Reels Bot
- Новый провайдер облачных телефонов (кроме GeeLark/DuoPlus)
- Новый метод автоматизации (Playwright, Puppeteer)

#### C) Analytics Module
**Цель:** Сбор статистики загруженных видео
- Tracking TikTok/YouTube/Instagram stats
- Dashboard для аналитики
- API для получения метрик

#### D) Account Management Module
**Цель:** Централизованное управление аккаунтами
- Единая база для TikTok/YouTube/Instagram аккаунтов
- Автоматическая ротация аккаунтов
- Proxy management

---

## 🏗️ Архитектура интеграции

### Текущая архитектура:

```
┌─────────────────────────────────────────────────────────┐
│  Main Project (tiktok-uploader-back)                    │
│                                                          │
│  ├─ Instagram Reels Bot (Python)                        │
│  │  └─ Cloud Phone APIs (GeeLark, DuoPlus)             │
│  │                                                       │
│  ├─ TikTok Backend (Node.js + Selenium)                 │
│  │  ├─ Server: 217.198.12.144:3000                     │
│  │  └─ Submodule: influence1                           │
│  │                                                       │
│  ├─ YouTube Backend (External)                          │
│  │  └─ Server: 72.56.76.237:3000                       │
│  │                                                       │
│  └─ Frontend (React)                                    │
│     ├─ TikTok UI                                        │
│     ├─ YouTube UI                                       │
│     └─ Submodule: influence2                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Предлагаемая архитектура (с новым модулем):

```
┌─────────────────────────────────────────────────────────┐
│  Main Project (tiktok-uploader-back)                    │
│                                                          │
│  ├─ Instagram Reels Bot (Python)                        │
│  │                                                       │
│  ├─ TikTok Backend (Node.js)                            │
│  │                                                       │
│  ├─ YouTube Backend (External → Migrate to Timeweb)     │
│  │                                                       │
│  ├─ Frontend (React)                                    │
│  │                                                       │
│  └─ [NEW MODULE]  ← ❓ Где и как встроить?              │
│     └─ Integration points                               │
│         ├─ API endpoints                                │
│         ├─ Shared services                              │
│         └─ Database schema                              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📋 План интеграции (Template)

### Phase 1: Research & Planning
- [ ] Определить требования к новому модулю
- [ ] Изучить существующую кодовую базу
- [ ] Определить точки интеграции (API, services, DB)
- [ ] Выбрать технологический стек (Python/TypeScript/Both)

### Phase 2: Architecture Design
- [ ] Спроектировать API endpoints
- [ ] Определить структуру базы данных (если нужно)
- [ ] Создать диаграмму зависимостей
- [ ] Определить shared services/utilities

### Phase 3: Implementation
- [ ] Создать модуль в `/home/user/webapp/[module-name]/`
- [ ] Реализовать core functionality
- [ ] Создать API endpoints в backend
- [ ] Обновить frontend (если нужно UI)

### Phase 4: Integration
- [ ] Интегрировать с существующими модулями
- [ ] Создать shared services (если нужно)
- [ ] Обновить database schema (если нужно)
- [ ] Настроить routing и middleware

### Phase 5: Testing
- [ ] Unit tests для нового модуля
- [ ] Integration tests с существующими модулями
- [ ] End-to-end testing
- [ ] Performance testing

### Phase 6: Documentation
- [ ] Обновить TECHNICAL_STRUCTURE.md
- [ ] Обновить PROJECT_SUMMARY.md
- [ ] Создать README для нового модуля
- [ ] Обновить API documentation

### Phase 7: Deployment
- [ ] Настроить deployment на Timeweb Cloud
- [ ] Обновить environment variables
- [ ] Настроить monitoring и logging
- [ ] Deploy и production testing

---

## 🔑 Ключевые вопросы к пользователю

1. **Какой модуль нужно встроить?**
   - Название модуля
   - Основная функциональность
   - Ссылка на репозиторий (если есть)

2. **Какие технологии использовать?**
   - Python или TypeScript?
   - Нужна ли база данных?
   - Нужен ли отдельный API?

3. **Интеграция с существующими модулями:**
   - С какими модулями взаимодействовать?
   - Какие данные обмениваться?
   - Какие API endpoints нужны?

4. **UI Requirements:**
   - Нужен ли UI в React frontend?
   - Какие страницы добавить?
   - Какие компоненты создать?

5. **Deployment:**
   - Где хостить? (Timeweb Cloud или отдельный сервер)
   - Какой порт использовать?
   - Какие environment variables нужны?

---

## 📚 Полезные ссылки

- **Main Repo:** `https://github.com/Synth-Nova/tiktok-uploader-back`
- **Backend Repo:** `https://github.com/Synth-Nova/influence1`
- **Frontend Repo:** `https://github.com/Synth-Nova/influence2`
- **Timeweb Cloud:** ID 6186087 (Influence Dev)
- **TikTok API:** `http://217.198.12.144:3000`
- **YouTube API:** `http://72.56.76.237:3000`

**Documentation:**
- `TECHNICAL_STRUCTURE.md` - полная структура проекта
- `ARCHITECTURE_DIAGRAM.md` - диаграммы архитектуры
- `PROJECT_SUMMARY.md` - краткая сводка проекта
- `TIKTOK_UPLOADER_DOCS.md` - документация TikTok/YouTube uploader
- `MODULE_INTEGRATION_PLAN.md` - этот файл

---

**Следующий шаг:** Ожидаем от пользователя информацию о модуле, который нужно встроить.
