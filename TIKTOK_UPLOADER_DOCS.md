# 📱 Multi-Platform Video Uploader - Technical Documentation

**Проект:** Автоматическая загрузка видео в TikTok и YouTube  
**Технологии:** TypeScript, Node.js, Selenium WebDriver, Bull Queue, Redis, Prisma  
**Статус:** Отдельный проект (не используется в Instagram Reels Uploader)  
**Расположение:** `/home/user/webapp/my-tiktok-uploader/`  
**Timeweb Cloud:** ID 6186087 (Influence Dev)  
**Production Server:** `http://217.198.12.144:3000`

---

## 🔗 GitHub Repositories

**Influence Dev Project** (Timeweb Cloud ID: 6186087) состоит из 3 репозиториев:

### 1️⃣ Main Repository (tiktok-uploader-back)
- **URL:** `https://github.com/Synth-Nova/tiktok-uploader-back`
- **Contains:** Root project, Instagram Reels bot, documentation
- **Branch:** `main`
- **Git Remote:** `origin`

### 2️⃣ Backend Repository (influence1) 
- **URL:** `https://github.com/Synth-Nova/influence1`
- **Location:** `/home/user/webapp/my-tiktok-uploader/backend`
- **Contains:** TikTok uploader API (TypeScript + Selenium + Bull Queue)
- **Production:** `http://217.198.12.144:3000` (Timeweb Cloud)
- **Submodule:** Embedded in main repository

### 3️⃣ Frontend Repository (influence2)
- **URL:** `https://github.com/Synth-Nova/influence2`
- **Location:** `/home/user/webapp/my-tiktok-uploader/frontend`
- **Contains:** React UI for TikTok/YouTube uploaders
- **Stack:** React + TypeScript + SCSS
- **Submodule:** Embedded in main repository

**⚠️ Important:** Backend and frontend are **git submodules** - separate repositories within the main project.

---

## 🎯 Назначение проекта

Multi-Platform Video Uploader - это **автономный сервис** для автоматизации загрузки видео в **TikTok** и **YouTube** через веб-интерфейс с использованием Selenium WebDriver. Проект имеет backend (TypeScript/Node.js) и frontend (React).

### Поддерживаемые платформы:
- ✅ **TikTok** - основная платформа
- ✅ **YouTube** - дополнительная платформа (separate backend server)

**⚠️ ВАЖНО:** Этот проект **отдельный** от Instagram Reels Uploader и использует другой подход - Selenium для автоматизации браузера вместо API облачных телефонов.

---

## 📂 Структура проекта

```
my-tiktok-uploader/
├── backend/                          # Node.js/TypeScript API (TikTok)
│   ├── src/
│   │   ├── controllers/              # API контроллеры
│   │   │   ├── account.controller.ts
│   │   │   ├── batch.controller.ts
│   │   │   ├── download.controller.ts
│   │   │   ├── stats.controller.ts
│   │   │   └── video.controller.ts
│   │   ├── routes/                   # Express маршруты
│   │   │   ├── account.routes.ts
│   │   │   ├── batch.routes.ts
│   │   │   ├── download.routes.ts
│   │   │   ├── stats.routes.ts
│   │   │   ├── video.routes.ts
│   │   │   └── index.ts
│   │   ├── services/                 # Бизнес-логика
│   │   │   ├── account.service.ts
│   │   │   ├── batch.service.ts
│   │   │   ├── upload.service.ts
│   │   │   └── video.service.ts
│   │   ├── workers/                  # Background workers
│   │   │   ├── upload.worker.ts
│   │   │   └── stats.worker.ts
│   │   ├── queues/                   # Bull queues
│   │   │   ├── upload.queue.ts
│   │   │   └── stats.queue.ts
│   │   ├── utils/                    # Утилиты
│   │   │   └── chrome-cleanup.ts
│   │   ├── scripts/                  # CLI скрипты
│   │   │   ├── clear-queue.ts
│   │   │   ├── clear-stats-queue.ts
│   │   │   ├── flush-redis.ts
│   │   │   ├── kill-chrome.ts
│   │   │   ├── view-queue.ts
│   │   │   └── view-stats-queue.ts
│   │   ├── tiktok-uploader.ts        # ⭐ Основной класс Selenium
│   │   ├── utils.ts                  # Общие утилиты
│   │   ├── server.ts                 # Express сервер
│   │   ├── worker.ts                 # Worker entry point
│   │   └── prisma.ts                 # Prisma client
│   ├── prisma/                       # Database schema
│   └── package.json
│
└── frontend/                         # React frontend
    ├── src/
    │   ├── pages/
    │   │   ├── Upload/               # ⭐ TikTok upload
    │   │   ├── UploadYoutube/        # ⭐ YouTube upload
    │   │   ├── History/              # TikTok history
    │   │   ├── HistoryYoutube/       # YouTube history
    │   │   ├── Accounts/             # Account management
    │   │   ├── Stats/                # Statistics
    │   │   ├── Uniquifier/           # Video uniquifier
    │   │   ├── Dashboard/            # Main dashboard
    │   │   └── Login/                # Authentication
    │   ├── services/
    │   │   ├── api.ts                # ⭐ TikTok API client
    │   │   └── youtube-api.ts        # ⭐ YouTube API client
    │   └── components/               # UI components
    ├── public/
    └── package.json
```

---

## 🏗️ Deployment Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Timeweb Cloud (ID: 6186087) - Influence Dev                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  TikTok Backend: 217.198.12.144:3000                    │ │
│  │  Repository: https://github.com/Synth-Nova/influence1   │ │
│  │  ├─ TikTok Uploader API (Express + TypeScript)         │ │
│  │  ├─ Selenium WebDriver (Chrome automation)             │ │
│  │  ├─ Bull Queue + Redis (task management)               │ │
│  │  ├─ Prisma + PostgreSQL (database)                     │ │
│  │  └─ 33 TypeScript files, 5 controllers, 4 services     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  React Frontend                                         │ │
│  │  Repository: https://github.com/Synth-Nova/influence2   │ │
│  │  ├─ TikTok Upload UI (/upload)                         │ │
│  │  ├─ YouTube Upload UI (/upload-youtube)                │ │
│  │  ├─ History & Stats Dashboard                          │ │
│  │  ├─ API Client: api.ts → 217.198.12.144:3000           │ │
│  │  └─ API Client: youtube-api.ts → 72.56.76.237:3000     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  External YouTube Server: 72.56.76.237:3000 (Old Server)     │
│  ├─ YouTube Upload API (Selenium)                            │
│  └─ TODO: Migrate to Timeweb Cloud                           │
└───────────────────────────────────────────────────────────────┘
```

### Repository Structure

```
Main Repo (tiktok-uploader-back)
├── .git/                                 # Main repository
├── instagram-reels-bot/                  # Instagram automation (Python)
├── my-tiktok-uploader/                   # TikTok/YouTube platform
│   ├── backend/                          # Submodule: influence1
│   │   └── .git/                         # Points to influence1 repo
│   └── frontend/                         # Submodule: influence2
│       └── .git/                         # Points to influence2 repo
├── TECHNICAL_STRUCTURE.md                # Project documentation
├── PROJECT_SUMMARY.md
└── TIKTOK_UPLOADER_DOCS.md              # This file
```

### Git Workflow

```bash
# Main repository
cd /home/user/webapp
git remote -v
# origin  https://github.com/Synth-Nova/tiktok-uploader-back.git

# Backend submodule
cd my-tiktok-uploader/backend
git remote -v
# origin  https://github.com/Synth-Nova/influence1.git

# Frontend submodule
cd ../frontend
git remote -v
# origin  https://github.com/Synth-Nova/influence2.git
```

---

## 🔧 Технический стек

### Backend
- **TypeScript** - типизированный JavaScript
- **Node.js/Express** - REST API сервер
- **Selenium WebDriver** - автоматизация браузера
- **ChromeDriver** - драйвер для Chrome
- **Bull** - очереди задач
- **Redis** - хранилище очередей
- **Prisma** - ORM для базы данных
- **Multer** - загрузка файлов

### Frontend
- **React** - UI фреймворк
- **TypeScript** - типизация
- (детали frontend не изучены)

---

## 🎬 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Platform Video Uploader System               │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌─────▼─────┐      ┌──────▼──────┐     ┌─────▼─────┐
  │  Frontend │      │   Backend   │     │   Redis   │
  │  (React)  │◄────►│  (Express)  │◄───►│  (Queue)  │
  │           │      │             │     │           │
  │  TikTok   │      │  TikTok API │     └───────────┘
  │  YouTube  │      │             │
  └───────────┘      └─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌─────▼─────┐      ┌──────▼──────┐     ┌─────▼─────┐
  │   Bull    │      │   Prisma    │     │  Chrome   │
  │  Workers  │      │  (Database) │     │ (Selenium)│
  └───────────┘      └─────────────┘     └───────────┘
                                                │
                            ┌───────────────────┼───────────────────┐
                            │                   │                   │
                      ┌─────▼─────┐      ┌──────▼──────┐
                      │ TikTok.com│      │ YouTube.com │
                      │  (Web UI) │      │  (Web UI)   │
                      └───────────┘      └─────────────┘
                      
                      
┌─────────────────────────────────────────────────────────────────┐
│                    YouTube Integration                          │
└─────────────────────────────────────────────────────────────────┘

Frontend (React)
     │
     ├─ youtube-api.ts ──────┐
     │                       │
     ▼                       ▼
YouTube API Client    YouTube Backend Server
(Separate Server)     (http://72.56.76.237:3000)
     │
     ├─ POST /api/batch-upload  # Массовая загрузка
     ├─ GET  /api/batch/all     # Список батчей
     │
     ▼
YouTube Automation
(Selenium или API)
```

---

## 🎥 YouTube Integration

### YouTube API Client (`youtube-api.ts`)

**Backend Server:** `http://72.56.76.237:3000` (отдельный сервер)

**Endpoints:**

```typescript
// Массовая загрузка видео на YouTube
POST /api/batch-upload
  - videos: File (ZIP с .mp4 файлами)
  - accounts: File (JSON с аккаунтами)
  - proxies: File (список proxy)
  - hashtag: string (опционально)
  - description: string (опционально)

// Получить список батчей
GET /api/batch/all
  Response: {
    success: boolean;
    batches: YoutubeUploadBatch[];
  }
```

**Interface:**
```typescript
interface YoutubeUploadBatch {
  id: string;
  videoPath: string;
  accountsPath: string;
  proxiesPath: string | null;
  hashtag: string | null;
  description: string | null;
  status: "PROCESSING" | "COMPLETED";
  videosLinks: string[];
  countCompletedVideos: number;
  countFailedVideos: number;
  countTotalVideos: number;
  accountsCount: number;
}
```

**Frontend Pages:**
- `/upload-youtube` - Загрузка видео на YouTube
- `/history-youtube` - История загрузок YouTube

**Особенности:**
- Отдельный backend server (не локальный)
- Поддержка массовой загрузки через ZIP архивы
- Управление аккаунтами и proxy
- Tracking статуса загрузки

---

## 🔑 Основные компоненты

### 1️⃣ **TikTokUploader Class** (`tiktok-uploader.ts`)
**Назначение:** Основной класс для автоматизации загрузки видео в TikTok

**Возможности:**
```typescript
export class TikTokUploader {
  // Инициализация браузера
  async initialize(): Promise<void>
  
  // Авторизация в TikTok
  async login(): Promise<void>
  
  // Загрузка одного видео
  async upload(config: VideoConfig): Promise<void>
  
  // Закрытие браузера
  async close(): Promise<void>
  
  // Скриншоты для отладки
  private async takeScreenshot(name: string): Promise<void>
}

interface VideoConfig {
  videoPath: string;    // Путь к видео файлу
  caption: string;      // Описание видео
  hashtags: string[];   // Хештеги
}
```

**Особенности:**
- Использует Selenium WebDriver для управления Chrome
- Поддержка proxy для разных геолокаций
- Headless режим (без GUI)
- Human-like typing/clicking (антидетект)
- Автоматические скриншоты для отладки
- Уникальные Chrome профили для каждой сессии

---

### 2️⃣ **Upload Queue** (`upload.queue.ts`)
**Назначение:** Очередь задач для загрузки видео

**Использование Bull Queue:**
```typescript
import Bull from 'bull';

const uploadQueue = new Bull('upload-queue', {
  redis: {
    host: process.env.REDIS_HOST,
    port: parseInt(process.env.REDIS_PORT || '6379')
  }
});

// Добавление задачи в очередь
await uploadQueue.add('upload-video', {
  accountId: '...',
  videoPath: '...',
  caption: '...',
  hashtags: [...]
});
```

**Workers обрабатывают задачи:**
- `upload.worker.ts` - загрузка видео
- `stats.worker.ts` - сбор статистики

---

### 3️⃣ **API Controllers**

#### Account Controller (`account.controller.ts`)
```typescript
POST   /api/accounts        # Создать аккаунт TikTok
GET    /api/accounts        # Список аккаунтов
GET    /api/accounts/:id    # Получить аккаунт
PUT    /api/accounts/:id    # Обновить аккаунт
DELETE /api/accounts/:id    # Удалить аккаунт
```

#### Video Controller (`video.controller.ts`)
```typescript
POST   /api/videos/upload   # Загрузить видео
GET    /api/videos          # Список загруженных видео
GET    /api/videos/:id      # Информация о видео
```

#### Batch Controller (`batch.controller.ts`)
```typescript
POST   /api/batch/upload    # Массовая загрузка (Excel файл)
GET    /api/batch/status    # Статус пакетной загрузки
```

#### Stats Controller (`stats.controller.ts`)
```typescript
GET    /api/stats           # Статистика загрузок
GET    /api/stats/:id       # Статистика по видео
```

---

### 4️⃣ **Services (Бизнес-логика)**

#### Upload Service (`upload.service.ts`)
- Валидация видео файлов
- Добавление задач в очередь
- Управление загрузкой

#### Account Service (`account.service.ts`)
- CRUD операции с аккаунтами TikTok
- Хранение credentials
- Управление sessions

#### Video Service (`video.service.ts`)
- Управление видео файлами
- Метаданные видео
- История загрузок

#### Batch Service (`batch.service.ts`)
- Парсинг Excel файлов с видео
- Массовая загрузка
- Прогресс tracking

---

### 5️⃣ **Utilities**

#### Human-like interactions (`utils.ts`)
```typescript
// Человекоподобный ввод текста
async function humanLikeTyping(
  element: WebElement,
  text: string
): Promise<void>

// Человекоподобный клик
async function humanLikeClick(
  driver: WebDriver,
  element: WebElement
): Promise<void>

// Случайная задержка
async function randomDelay(
  min: number = 1000,
  max: number = 3000
): Promise<void>
```

#### Chrome Cleanup (`chrome-cleanup.ts`)
- Автоматическая очистка зависших процессов Chrome
- Удаление временных профилей
- Memory management

---

## 📊 Database Schema (Prisma)

```prisma
model Account {
  id          String    @id @default(cuid())
  username    String    @unique
  password    String
  proxy       String?
  userAgent   String?
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
  
  videos      Video[]
}

model Video {
  id          String    @id @default(cuid())
  accountId   String
  account     Account   @relation(fields: [accountId], references: [id])
  
  filePath    String
  caption     String
  hashtags    String[]
  
  status      String    @default("pending") // pending, uploading, completed, failed
  uploadedAt  DateTime?
  error       String?
  
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
}

model UploadStats {
  id          String    @id @default(cuid())
  videoId     String    @unique
  
  views       Int       @default(0)
  likes       Int       @default(0)
  comments    Int       @default(0)
  shares      Int       @default(0)
  
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
}
```

---

## 🚀 Использование

### Запуск Backend
```bash
cd /home/user/webapp/my-tiktok-uploader/backend

# Development
yarn dev

# Production
yarn build
yarn start

# С чистой очередью
yarn dev:clean
```

### CLI Scripts
```bash
# Просмотр очереди
yarn queue:view

# Очистить очередь
yarn queue:clear

# Просмотр статистики
yarn stats-queue:view

# Убить зависшие процессы Chrome
yarn chrome:kill

# Очистить Redis
yarn redis:flush
```

---

## 🔄 Workflow загрузки видео

```
1. Frontend/API
     │
     ├─ POST /api/videos/upload
     │  - Загрузить видео файл
     │  - Указать caption, hashtags
     │  - Выбрать аккаунт TikTok
     │
     ▼
2. Upload Controller
     │
     ├─ Валидация файла
     ├─ Сохранение в /uploads
     │
     ▼
3. Upload Queue (Bull)
     │
     ├─ Добавить задачу в Redis
     │
     ▼
4. Upload Worker
     │
     ├─ Получить задачу из очереди
     ├─ Создать TikTokUploader instance
     │
     ▼
5. TikTokUploader
     │
     ├─ Initialize Chrome (Selenium)
     ├─ Login to TikTok
     ├─ Navigate to upload page
     ├─ Select video file
     ├─ Fill caption & hashtags
     ├─ Click "Post"
     ├─ Wait for completion
     │
     ▼
6. Stats Collection
     │
     ├─ Добавить задачу в stats queue
     ├─ Периодический сбор views/likes
     │
     ▼
7. Database Update
     │
     ├─ status = "completed"
     ├─ uploadedAt = now()
     │
     ▼
8. Frontend/API Response
     │
     └─ ✅ Success / ❌ Error
```

---

## 🆚 Сравнение с Instagram Reels Uploader

| Критерий | Multi-Platform Uploader | Instagram Reels Uploader |
|----------|------------------------|--------------------------|
| **Платформы** | TikTok + YouTube | Instagram |
| **Подход** | Selenium (браузер) | Cloud Phone API (GeeLark, DuoPlus) |
| **Технологии** | TypeScript, Node.js | Python |
| **Автоматизация** | WebDriver | RPA API / Playwright |
| **Масштабирование** | Ограничено (много Chrome) | Лучше (облачные телефоны) |
| **Стабильность** | Зависит от UI TikTok/YouTube | Зависит от API |
| **Скорость** | Медленнее (UI) | Быстрее (API) |
| **Антидетект** | User-Agent, Proxy, delays | Cloud Phone fingerprints |
| **Video Processing** | ❌ Нет (только frontend) | ✅ Uniquifier v2.0 |
| **Background Uniquifier** | ❌ Нет | ✅ v2.0 |
| **YouTube Support** | ✅ Да | ❌ Нет |

---

## ⚠️ Ограничения и проблемы

### 1️⃣ **Selenium проблемы:**
- TikTok/YouTube могут детектировать автоматизацию
- Требуется много ресурсов (Chrome processes)
- Нестабильно при изменении UI TikTok/YouTube
- Captcha могут блокировать

### 2️⃣ **Масштабирование:**
- Каждая загрузка = отдельный Chrome процесс
- Memory intensive
- Сложно запускать много параллельных загрузок

### 3️⃣ **Maintenance:**
- Требуется обновление селекторов при изменении TikTok/YouTube UI
- Selenium версии должны совпадать с ChromeDriver

### 4️⃣ **YouTube Integration:**
- Использует ОТДЕЛЬНЫЙ backend server (`http://72.56.76.237:3000`)
- Требует доступ к внешнему серверу
- Зависимость от внешней инфраструктуры

---

## 🎯 Для чего этот проект НЕ используется

**Multi-Platform Uploader НЕ используется** в текущем Instagram Reels Uploader проекте, потому что:

1. **Разные платформы:** TikTok/YouTube vs Instagram
2. **Разный подход:** Selenium vs Cloud Phone API
3. **Разные цели:** Простая загрузка vs массовая автоматизация с уникализацией
4. **Нет video processing:** Multi-Platform Uploader не имеет встроенного Uniquifier
5. **YouTube требует отдельный сервер:** Не локальное решение

---

## 💡 Возможное использование

Multi-Platform Uploader **может быть полезен**, если:

1. Нужна загрузка в **TikTok** (не Instagram)
2. Нужна загрузка в **YouTube** (дополнительная платформа)
3. Нет доступа к TikTok/YouTube API
4. Требуется простая автоматизация через UI
5. Достаточно небольших объемов загрузок

---

## 📝 Рекомендации

### Если нужна интеграция с Instagram Reels Uploader:

1. **Можно использовать Video Uniquifier** из Instagram Reels Uploader:
   - Копировать `src/tools/video_uniquifier.py`
   - Интегрировать в TikTok/YouTube Uploader workflow
   - Обрабатывать видео перед загрузкой

2. **Можно использовать Background Uniquifier**:
   - Создавать уникальные фоны для TikTok/YouTube
   - Применить ту же схему (8 спикеров × 24 языка)

3. **НО лучше использовать Cloud Phone подход**:
   - Искать TikTok/YouTube Cloud Phone API (если есть)
   - Использовать подход как с GeeLark/DuoPlus
   - Более стабильно и масштабируемо

---

## 🔗 Полезные ссылки

### TikTok
- **TikTok Web:** https://www.tiktok.com/
- **TikTok Creator Portal:** https://www.tiktok.com/creators/

### YouTube
- **YouTube Web:** https://www.youtube.com/
- **YouTube Studio:** https://studio.youtube.com/
- **YouTube API:** https://developers.google.com/youtube/v3

### Технологии
- **Selenium WebDriver Docs:** https://www.selenium.dev/documentation/
- **Bull Queue Docs:** https://github.com/OptimalBits/bull
- **Prisma Docs:** https://www.prisma.io/docs/

---

## 📊 Статистика проекта

### Code Statistics
- **TypeScript файлов:** 33 (backend)
- **Основных компонентов:**
  - Controllers: 5
  - Routes: 5
  - Services: 4
  - Workers: 2
  - Queues: 2
  - Scripts: 6
  - Frontend Pages: 9 (включая TikTok и YouTube)
- **Dependencies:** 15+ (Selenium, Bull, Prisma, Express, React, etc.)

### Platform Support
- ✅ **TikTok** - Основная платформа (локальный backend)
- ✅ **YouTube** - Дополнительная платформа (отдельный backend: `http://72.56.76.237:3000`)
- ❌ **Instagram** - Не поддерживается (см. Instagram Reels Uploader)

### Frontend Pages
1. **Upload** - TikTok загрузка
2. **UploadYoutube** - YouTube загрузка
3. **History** - TikTok история
4. **HistoryYoutube** - YouTube история
5. **Accounts** - Управление аккаунтами
6. **Stats** - Статистика
7. **Uniquifier** - Video uniquifier (frontend only)
8. **Dashboard** - Главная панель
9. **Login** - Авторизация

---

## 🎓 Выводы

**Multi-Platform Uploader** - это **отдельный проект** для автоматизации загрузки видео в **TikTok** и **YouTube** через Selenium. Он **НЕ используется** в текущем Instagram Reels Uploader, который использует более продвинутый подход с Cloud Phone API и Video Uniquification.

**Если нужна загрузка в TikTok/YouTube:**
- Можно использовать этот проект как есть
- Или адаптировать Cloud Phone подход из Instagram Reels Uploader

**Если нужна загрузка в Instagram:**
- Используйте Instagram Reels Uploader с GeeLark/DuoPlus API
- Не используйте Multi-Platform Uploader

**Архитектурные различия:**
- **TikTok/YouTube Uploader:** Selenium (браузерная автоматизация)
- **Instagram Reels Uploader:** Cloud Phone API (RPA автоматизация)
- **TikTok/YouTube** имеет интеграцию с двумя платформами
- **YouTube** требует отдельный backend server

---

**Конец документации**

**См. также:**
- `TECHNICAL_STRUCTURE.md` - Instagram Reels Uploader структура
- `ARCHITECTURE_DIAGRAM.md` - Instagram Reels Uploader архитектура
- `PROJECT_SUMMARY.md` - Общий обзор Instagram проекта

**Ключевые отличия проектов:**
- **Multi-Platform Uploader:** TikTok + YouTube (Selenium)
- **Instagram Reels Uploader:** Instagram (Cloud Phone API + Video Uniquifier)
