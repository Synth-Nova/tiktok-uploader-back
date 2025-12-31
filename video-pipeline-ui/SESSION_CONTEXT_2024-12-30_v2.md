# 🚀 SynthNova Session Context — 30.12.2024 v2
**Последнее обновление:** 30.12.2024 17:30 UTC

---

## 📍 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ ЧТО РАБОТАЕТ:

| Компонент | Статус | URL/Порт |
|-----------|--------|----------|
| Video Cutter API (Flask) | ✅ Запущен | localhost:8090, prefix `/cutter` |
| Influence Backend API | ✅ Запущен | https://upl.synthnova.me (порт 3000) |
| UI Dashboard | ✅ Работает | https://8888-*.sandbox.novita.ai |
| Нарезка видео | ✅ Готово | POST /cutter/cut |
| Уникализация | ✅ Готово | POST /cutter/uniquify |
| Добавление звука | ✅ Готово | POST /cutter/add-sound |
| ZIP архивация | ✅ Готово | POST /cutter/create-zip |
| Batch Upload | ✅ Готово | POST /api/batch-upload |
| SSE Tracking | ✅ Готово | GET /api/batches/{id}/stream |
| DarkShop интеграция | ✅ Готово | POST /api/darkshop/purchase |
| PX6 прокси | ✅ Готово | POST /api/px6/buy |

### ⚠️ ЧАСТИЧНО РАБОТАЕТ:

| Компонент | Проблема | Решение |
|-----------|----------|---------|
| Заливка в TikTok | "Не удалось извлечь sessionId из cookies" | Нужен логин через email/password |
| PX6 баланс | Ошибка 300 | Пополнить баланс или использовать Bright Data |

### ❌ НЕ РЕАЛИЗОВАНО:

| Функционал | Статус | Что нужно |
|------------|--------|-----------|
| Логин по email/password с капчей | ❌ НЕТ | 2captcha/anticaptcha API ключ |
| Email verification | ❌ НЕТ | IMAP доступ к почте аккаунтов |
| Статистика публикаций | ❌ НЕТ | Selenium парсинг TikTok |

---

## 🔑 ГЛАВНАЯ ПРОБЛЕМА: Авторизация TikTok аккаунтов

### Текущее состояние:
- В БД есть 12 аккаунтов с email/password (но без cookies)
- Код логина **СУЩЕСТВУЕТ** в `tiktok-uploader.ts:288-412`
- Код идёт на страницу `https://www.tiktok.com/login/phone-or-email/email`
- **НО** код НЕ умеет решать капчу и проверять email verification

### Где код логина:
```
/opt/influence-backend/src/tiktok-uploader.ts:288  → async login(): Promise<void>
/opt/influence-backend/src/services/warming.service.ts:245 → private async login()
/opt/influence-backend/src/workers/upload.worker.ts:75 → await uploader.login()
```

### Что нужно добавить:
1. **Captcha Solver** (2captcha API: ~$3 за 1000 капч)
2. **Email Verification** (IMAP доступ к почте)
3. **Session сохранение** (cookies после логина)

---

## 📂 СТРУКТУРА ПРОЕКТА

### Sandbox (/home/user/webapp):
```
/home/user/webapp/
├── backend/
│   └── video_cutter_v5.py        ← Главный API нарезки (1838 строк)
├── video-pipeline-ui/
│   └── index.html                 ← UI Dashboard (все 7 шагов)
├── video_cutter_server.py         ← Flask сервер (порт 8090)
├── outputs/                       ← Папка с видео/ZIP
└── uploads/                       ← Загруженные файлы
```

### Сервер upl.synthnova.me (/opt/influence-backend):
```
/opt/influence-backend/
├── src/
│   ├── tiktok-uploader.ts         ← Класс TikTokUploader с login()
│   ├── services/
│   │   ├── batch.service.ts       ← Обработка батчей
│   │   ├── upload.service.ts      ← Валидация путей (ИСПРАВЛЕНО)
│   │   ├── darkshop.service.ts    ← DarkShop API
│   │   ├── px6.service.ts         ← PX6 прокси
│   │   └── warming.service.ts     ← Прогрев аккаунтов
│   ├── routes/
│   │   ├── batch.routes.ts
│   │   ├── darkshop.routes.ts
│   │   ├── px6.routes.ts
│   │   └── ... (15+ файлов)
│   └── workers/
│       ├── upload.worker.ts       ← Bull Queue воркер
│       └── stats.worker.ts
├── uploads/                       ← Временные файлы (ВАЖНО!)
└── .env.production                ← API ключи
```

---

## 🛠️ ИСПРАВЛЕНИЯ, СДЕЛАННЫЕ СЕГОДНЯ

### 1. Путь temp → uploads в upload.service.ts
```bash
# Было:
const safeBaseDir = path.resolve(__dirname, "../../temp");

# Стало:
const safeBaseDir = path.resolve(__dirname, "../../uploads");
```

### 2. Симлинк temp → uploads
```bash
ln -s /opt/influence-backend/uploads /opt/influence-backend/temp
```

### 3. UI: добавлен SSE tracking прогресса загрузки
- Файл: `/home/user/webapp/video-pipeline-ui/index.html`
- Добавлен `currentEventSource` для SSE
- Добавлен `pollBatchStatus()` как fallback

---

## 📡 API ENDPOINTS

### Video Cutter (localhost:8090):
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /cutter/cut | Нарезка видео |
| POST | /cutter/uniquify | Уникализация |
| POST | /cutter/add-sound | Добавить звук |
| POST | /cutter/add-sound-batch | Пакетное добавление звука |
| POST | /cutter/create-zip/{folder} | Создать ZIP |
| GET | /cutter/list-zips | Список ZIP |
| GET | /cutter/folders | Список папок |
| GET | /cutter/sounds | Библиотека звуков |
| POST | /cutter/parse-sound-url | Парсинг TikTok sound URL |

### Influence Backend (upl.synthnova.me):
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /api/batch-upload | Загрузка батча (multipart/form-data) |
| GET | /api/batches | Список батчей |
| GET | /api/batches/{id} | Детали батча |
| GET | /api/batches/{id}/stream | SSE прогресс |
| GET | /api/managed-accounts | Список аккаунтов |
| GET | /api/managed-accounts/stats | Статистика |
| GET | /api/darkshop/status | Баланс DarkShop |
| POST | /api/darkshop/purchase | Покупка аккаунтов |
| GET | /api/px6/status | Статус PX6 |
| POST | /api/px6/buy | Покупка прокси |
| GET | /api/proxies | Список прокси |

---

## 🔐 ДАННЫЕ АККАУНТОВ (пример из БД)

```json
{
  "id": "66898c29-810a-4233-8bf8-889cc5d1acae",
  "email": "mirasuarez@onet.pl",
  "password": "dilse@342345",
  "username": "mirasnocfcj",
  "backupCode": "dilse@342345",
  "platform": "tiktok",
  "country": "US",
  "status": "active",
  "proxyId": "a95c7d66-a3be-4bd2-a590-e12a4ace87db",
  "proxy": {
    "host": "196.17.64.168",
    "port": 8000,
    "country": "US"
  }
}
```

**Всего:** 12 аккаунтов, 12 прокси

---

## 📊 РЕСУРСЫ

| Ресурс | Значение | Статус |
|--------|----------|--------|
| TikTok аккаунты | 12 | ✅ Есть, но без cookies |
| Прокси PX6 | 12 | ✅ Привязаны к аккаунтам |
| DarkShop баланс | ~536₽ | ✅ Достаточно |
| PX6 баланс | 781₽ | ⚠️ Ошибка 300 |
| Anthropic API | ~$42 | ✅ До Dec 2026 |

---

## 🔄 PIPELINE FLOW

```
1. Загрузка видео → POST /cutter/cut
2. Уникализация → POST /cutter/uniquify
3. Парсинг Sound ID → POST /cutter/parse-sound-url
4. Добавление звука → POST /cutter/add-sound-batch
5. Создание ZIP → POST /cutter/create-zip/{folder}
6. UI: Выбор аккаунтов + прокси
7. Загрузка в TikTok → POST /api/batch-upload
   ↓
   Проблема: "Не удалось извлечь sessionId из cookies"
   ↓
   Нужен логин с капчей + email verification
```

---

## 🚨 СЛЕДУЮЩИЕ ШАГИ (ПРИОРИТЕТ)

### 1. [КРИТИЧНО] Реализовать логин с капчей
```typescript
// Нужно в tiktok-uploader.ts добавить:
import { TwoCaptcha } from '2captcha';

async solveCaptcha(siteKey: string): Promise<string> {
  const solver = new TwoCaptcha('API_KEY');
  const result = await solver.hcaptcha({
    sitekey: siteKey,
    pageurl: 'https://www.tiktok.com/login'
  });
  return result.data;
}
```

### 2. [КРИТИЧНО] Email verification через IMAP
```typescript
// Нужно добавить:
import Imap from 'imap';

async getEmailCode(email: string, password: string): Promise<string> {
  // Подключиться к IMAP
  // Найти письмо от TikTok
  // Извлечь 6-значный код
}
```

### 3. [ВАЖНО] Сохранение cookies после логина
```typescript
// После успешного логина:
const cookies = await page.context().cookies();
await saveCookiesToDB(accountId, cookies);
```

---

## 💻 КОМАНДЫ ДЛЯ ПРОДОЛЖЕНИЯ

### На сервере upl.synthnova.me:
```bash
# Логи API
pm2 logs influence-api --lines 50 --nostream

# Перезапуск API
pm2 restart influence-api --update-env

# Проверить код логина
cat /opt/influence-backend/src/tiktok-uploader.ts | grep -A 100 "async login"

# Найти все упоминания captcha
grep -rn "captcha\|2captcha" /opt/influence-backend/src/
```

### В sandbox:
```bash
# Запустить Video Cutter
cd /home/user/webapp && FLASK_APP=video_cutter_server.py flask run --host=0.0.0.0 --port=8090 &

# Тест API
curl -s http://localhost:8090/cutter/stats | jq

# Тест batch upload
curl -X POST https://upl.synthnova.me/api/batch-upload \
  -F "videos=@test.zip" \
  -F "accounts=@accounts.txt" \
  -F "proxies=@proxies.txt" \
  -F "caption=Test #fyp"
```

---

## 📁 ВАЖНЫЕ ФАЙЛЫ

### Код:
- `/home/user/webapp/backend/video_cutter_v5.py` — Video Cutter API
- `/home/user/webapp/video-pipeline-ui/index.html` — UI Dashboard
- `/opt/influence-backend/src/tiktok-uploader.ts` — TikTok логин/загрузка

### Документация:
- `/home/user/webapp/FULL_PIPELINE_MAP_2024-12-30.md` — Карта pipeline
- `/home/user/webapp/SESSION_CONTEXT_2024-12-30_v2.md` — Этот файл

### Логи:
- `/root/.pm2/logs/influence-api-out-0.log` — Логи на сервере

---

## 📌 ВОПРОСЫ ДЛЯ РАЗРАБОТЧИКОВ

1. **Где код для 2captcha/anticaptcha?** Разработчики сказали, что реализовали — но в коде его НЕТ
2. **Где код для email verification?** Тоже не найден
3. **Есть ли другой репозиторий?** Возможно, код в другом месте

---

**Конец контекста**
*Создано: 30.12.2024 17:30 UTC*
