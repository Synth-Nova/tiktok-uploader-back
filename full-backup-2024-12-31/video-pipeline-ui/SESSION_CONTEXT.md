# SynthNova Video Pipeline - Session Context
**Дата:** 2024-12-30  
**Версия:** v3  
**Сервер:** upl.synthnova.me

---

## Текущее состояние проекта

### Задеплоено на сервере (upl.synthnova.me)

#### Frontend (UI) - `/var/www/html/`
- **index.html** — Video Pipeline UI (v3)
- **accounts.html** — Менеджер аккаунтов (новый)

#### Backend - `/opt/influence-backend/`
- **DarkShop V2 интеграция** — работает (но автопокупка убрана из UI)
- **API эндпоинты:**
  - `GET /api/darkshop/status` — баланс DarkShop ✅
  - `GET /api/darkshop/products` — список товаров ✅
  - `GET /api/darkshop/products/cookies` — товары с cookies ✅
  - `POST /api/darkshop/purchase` — покупка (требует доработки order API)
  - `GET /api/managed-accounts` — список аккаунтов
  - `POST /api/managed-accounts/import` — импорт (TODO)

---

## Что сделано сегодня (30.12.2024)

### 1. DarkShop V2 интеграция
- Подключен API dark.shopping
- Баланс: ~478₽ (после тестовых покупок)
- Товары загружаются корректно
- Проблема: API dark.shopping не возвращает данные заказа после покупки (order/view не работает)

### 2. Модуль «Управление аккаунтами» (accounts.html)
Создан полноценный UI для управления аккаунтами:

**Платформы:**
- TikTok 🎵
- YouTube 📺  
- Instagram 📸

**Типы аккаунтов:**
- Cookie 🍪 — вход по cookies, быстрая верификация
- Login 🔐 — email/password + верификация по почте
- Autoreg 🤖 — свежие аккаунты, требуют прогрева

**Статусы:**
- new → verifying → verified → warming → ready → working
- Ветки: dead, banned

**Функционал UI:**
- Импорт аккаунтов массово (по типам)
- Фильтрация по платформе/типу/статусу/стране
- Поиск по email/username
- Массовые действия (проверка, прогрев, удаление)

### 3. Изменения в Pipeline UI
- Убрано модальное окно DarkShop для автопокупки
- Кнопки «Купить аккаунты» заменены на ссылки на accounts.html
- Раздел «Магазин» показывает информацию о типах аккаунтов

---

## TODO на завтра

### Высокий приоритет
1. **Backend API для accounts.html:**
   - `POST /api/managed-accounts/import` — импорт аккаунтов
   - `PUT /api/managed-accounts/:id/status` — обновление статуса
   - `DELETE /api/managed-accounts/:id` — удаление
   - `POST /api/managed-accounts/verify` — массовая верификация
   - `POST /api/managed-accounts/warm` — массовый прогрев

2. **Верификация аккаунтов:**
   - Cookie-акки: проверка валидности cookies через Playwright
   - Login-акки: вход + IMAP для кода из почты
   - Autoreg: проверка + базовый прогрев

### Средний приоритет
3. **Прогрев аккаунтов:**
   - Автоматические действия (просмотр видео, лайки)
   - Расписание прогрева
   - Мониторинг активности

4. **Instagram интеграция:**
   - Аналогичный пайплайн как для TikTok
   - Импорт/верификация аккаунтов

### Низкий приоритет
5. **YouTube интеграция:**
   - Управление каналами
   - Загрузка видео

---

## Архитектура базы данных

### Таблица `managedAccount` (существует)
```prisma
model ManagedAccount {
  id           String   @id @default(cuid())
  email        String?
  password     String?
  username     String?
  backupCode   String?
  cookies      String?  // JSON
  platform     String   // tiktok, youtube, instagram
  country      String?
  status       String   // new, verifying, verified, warming, ready, working, dead, banned
  type         String?  // cookie, login, autoreg
  proxyId      String?
  lastActionAt DateTime?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
}
```

---

## Файлы в sandbox

### Архивы для деплоя
- `video-pipeline-ui-v3.tar.gz` — UI Pipeline + accounts.html
- `darkshop-v2.tar.gz` — DarkShop сервис

### Директории
- `/home/user/webapp/video-pipeline-ui/` — исходники UI
- `/home/user/webapp/accounts-manager/` — исходники accounts.html
- `/home/user/webapp/darkshop-v2/` — DarkShop TypeScript сервис

---

## API ключи и эндпоинты

### DarkShop
- **API URL:** https://dark.shopping/api/v1
- **API Key:** 5487b48c4cb2cfc5c2b005fa9a98cfd83f644430
- **Документация:** https://dark.shopping/developer/index

### Backend
- **Production:** https://upl.synthnova.me
- **Local:** http://localhost:3000

---

## Команды для деплоя

### UI обновление
```bash
cd /opt/influence-backend
wget https://[sandbox-url]/video-pipeline-ui-v3.tar.gz
tar -xzf video-pipeline-ui-v3.tar.gz
cp video-pipeline-ui/index.html /var/www/html/index.html
cp video-pipeline-ui/accounts.html /var/www/html/accounts.html
```

### Backend обновление
```bash
cd /opt/influence-backend
# Скопировать файлы сервисов
npm run build
pm2 restart influence-api
```

---

## Заметки

1. **DarkShop order API** — не работает получение данных заказа. Возможно нужен другой endpoint или API возвращает данные только при создании.

2. **Прогрев аккаунтов** — нужен Playwright/Puppeteer для автоматизации действий в браузере.

3. **IMAP для почты** — нужен для верификации login-аккаунтов (получение кодов подтверждения).

4. **2captcha/anticaptcha** — может понадобиться для обхода капч при входе.

---

## Контакты / Ресурсы

- **Сервер:** upl.synthnova.me
- **PM2:** influence-api, influence-worker, video-editor-api, youtube-uploader
- **База:** Prisma (PostgreSQL)
