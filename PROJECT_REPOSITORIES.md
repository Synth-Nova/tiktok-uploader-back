# 📊 GitHub Repositories - Полная структура проектов

**Дата:** 2025-12-22  
**Автор:** AI Assistant + User clarification

---

## 🎯 ОСНОВНОЙ ПРОЕКТ (ID 5788751)

### Repository структура:

#### 1️⃣ Backend - influence1
- **URL:** `https://github.com/Synth-Nova/influence1`
- **Main Branch:** `main` (by @Synth-Nova)
- **Working Branch:** Created by @Christiangrandcrue (2 weeks ago)
- **Назначение:** TikTok Uploader Backend (TypeScript, Selenium, Bull Queue)
- **Status:** ✅ Production

#### 2️⃣ Frontend - influence2
- **URL:** `https://github.com/Synth-Nova/influence2`
- **Main Branch:** `main` (by @Synth-Nova)
- **Working Branch:** Created by @Christiangrandcrue (2 weeks ago)
- **Назначение:** React UI для TikTok/YouTube uploaders
- **Status:** ✅ Production

### Особенности:
- Основной проект состоит из **двух отдельных репозиториев**
- Backend и Frontend - **независимые** репозитории (не submodules!)
- Деплой на **Timeweb Cloud ID 5788751**

---

## 🔧 ФОРК ПРОЕКТА (ID 6186087) - Influence Dev

### Repository структура:

#### Main Repository - tiktok-uploader-back
- **URL:** `https://github.com/Synth-Nova/tiktok-uploader-back`
- **Назначение:** Wrapper repository с документацией + Instagram Reels Bot
- **Деплой:** Timeweb Cloud ID 6186087
- **Server:** `http://217.198.12.144:3000`

#### Submodules (embedded):
1. **Backend:** `influence1` (embedded as git submodule)
   - Location: `/home/user/webapp/my-tiktok-uploader/backend/`
   
2. **Frontend:** `influence2` (embedded as git submodule)
   - Location: `/home/user/webapp/my-tiktok-uploader/frontend/`

### Дополнительно:
- Instagram Reels Bot (Python) - `/home/user/webapp/instagram-reels-bot/`
- Video Uniquifier v2.0
- Comprehensive documentation

---

## 📐 Архитектура проектов

```
┌──────────────────────────────────────────────────────────────┐
│  ОСНОВНОЙ ПРОЕКТ (ID 5788751)                                │
│                                                               │
│  Repo 1: influence1 (Backend)                                │
│  └─ https://github.com/Synth-Nova/influence1                 │
│                                                               │
│  Repo 2: influence2 (Frontend)                               │
│  └─ https://github.com/Synth-Nova/influence2                 │
│                                                               │
│  Deployment: Отдельный (Timeweb ID 5788751)                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ФОРК ПРОЕКТА (ID 6186087) - Influence Dev                   │
│                                                               │
│  Main Repo: tiktok-uploader-back                             │
│  └─ https://github.com/Synth-Nova/tiktok-uploader-back       │
│      ├─ Instagram Reels Bot (Python)                         │
│      ├─ Documentation (TECHNICAL_STRUCTURE.md, etc.)         │
│      └─ Submodules:                                          │
│          ├─ my-tiktok-uploader/backend/  → influence1        │
│          └─ my-tiktok-uploader/frontend/ → influence2        │
│                                                               │
│  Deployment: http://217.198.12.144 (Timeweb ID 6186087)      │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔑 Ключевые отличия

### Основной проект (ID 5788751):
- ✅ 2 отдельных репозитория (influence1 + influence2)
- ✅ Чистая структура без wrapper
- ✅ Production deployment
- ⚠️ НЕ ВНОСИМ ИЗМЕНЕНИЯ без согласования!

### Форк (ID 6186087):
- ✅ 1 wrapper repository + 2 submodules
- ✅ Дополнительно: Instagram Reels Bot, Uniquifier
- ✅ Полная документация
- ✅ Development/Testing environment
- ✅ ВСЕ изменения здесь!

---

## 👤 Contributors

### @Synth-Nova
- Owner organization
- Main branches creator

### @Christiangrandcrue
- Active contributor
- Created working branches in influence1 and influence2 (2 weeks ago)

---

## 📝 Workflow

### Для разработки новых фич:
1. **Работаем в форке** (tiktok-uploader-back)
2. Изменения в submodules (influence1/influence2)
3. Тестируем на Timeweb ID 6186087
4. После успешного тестирования:
   - Push изменения в influence1/influence2
   - Pull в основной проект (ID 5788751)

### Для основного проекта:
1. Pull changes from influence1/influence2
2. Deploy на Timeweb ID 5788751
3. Production testing

---

## 🎬 Uniquifier Integration

**Цель:** Добавить Video Uniquifier в меню

**Где:** ТОЛЬКО в форке (tiktok-uploader-back)

**Почему:** Безопасное тестирование без риска для production

После успешного тестирования → можно перенести в основной проект

---

## 📚 Links

### Repositories:
- Main Backend: https://github.com/Synth-Nova/influence1
- Main Frontend: https://github.com/Synth-Nova/influence2
- Fork (wrapper): https://github.com/Synth-Nova/tiktok-uploader-back

### Deployments:
- Основной: Timeweb Cloud ID 5788751
- Форк: Timeweb Cloud ID 6186087 (http://217.198.12.144)

### Documentation:
- TECHNICAL_STRUCTURE.md - полная техническая структура
- UNIQUIFIER_INTEGRATION.md - план интеграции Uniquifier
- PROJECT_SUMMARY.md - краткая сводка
- PROJECT_REPOSITORIES.md - этот файл

---

**Последнее обновление:** 2025-12-22
