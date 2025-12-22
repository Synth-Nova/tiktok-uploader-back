# Instagram Reels Auto-Uploader Bot

Автоматическая система для загрузки Reels в Instagram с поддержкой:
- 🔐 Авто-логин с обработкой email-верификации (firstmail.ltd)
- 🌍 Anti-detect fingerprints по странам (US, GB, DE)
- 🔌 Proxy интеграция (Decodo Residential)
- 🍪 Сохранение сессий (cookies)
- 🎬 Автоматическая загрузка Reels

## Структура проекта

```
instagram-reels-bot/
├── config/              # Конфигурационные файлы
├── data/
│   ├── sessions/        # Сохранённые cookies
│   ├── uploads/         # Логи загрузок
│   └── videos/          # Видео для загрузки
├── scripts/
│   ├── run_automation.py    # Главный скрипт автоматизации
│   ├── batch_auto_login.py  # Пакетный логин
│   └── import_accounts.py   # Импорт аккаунтов в БД
├── src/
│   ├── core/
│   │   └── database.py      # SQLite база данных
│   ├── modules/
│   │   ├── auto_login.py        # Авто-логин + email верификация
│   │   ├── email_parser.py      # Парсер email для кодов
│   │   ├── reels_uploader.py    # Загрузчик Reels
│   │   ├── gologin_integration.py  # GoLogin API
│   │   └── instagram_auth.py    # Instagram авторизация
│   └── utils/
│       └── fingerprint_generator.py  # Генератор fingerprints
└── requirements.txt
```

## Установка

```bash
# Клонировать/скопировать проект
cd instagram-reels-bot

# Установить зависимости
pip install -r requirements.txt

# Установить Chrome (если не установлен)
# Ubuntu/Debian:
# apt-get install chromium-browser

# macOS:
# brew install --cask google-chrome
```

## Использование

### 1. Проверить статус аккаунтов

```bash
python scripts/run_automation.py --mode status
```

### 2. Залогинить все аккаунты

```bash
# Залогинить все 10 аккаунтов (с задержкой 60 сек)
python scripts/run_automation.py --mode login-all --delay 60
```

Процесс:
1. Открывает браузер с anti-detect fingerprint
2. Использует прокси по стране аккаунта
3. Вводит логин/пароль
4. Если нужен код верификации - автоматически получает из email (firstmail.ltd)
5. Сохраняет cookies в `data/sessions/`

### 3. Загрузить Reels

```bash
# Загрузить видео на все аккаунты
python scripts/run_automation.py --mode upload --video-dir ./data/videos --delay 120
```

### 4. Тест одного аккаунта

```bash
python scripts/run_automation.py --mode test --username charleshenry19141
```

## Конфигурация аккаунтов

Аккаунты настроены в `scripts/run_automation.py`:

```python
ACCOUNTS_CONFIG = [
    {
        'username': 'accountname',
        'password': 'password',
        'email': 'email@domain.com',
        'email_password': 'email_password',
        'country': 'us',  # us, gb, de
        'proxy': {
            'host': 'us.decodo.com',
            'port': 10001,
            'user': 'proxy_user',
            'password': 'proxy_pass'
        },
        'video': 'video_us.mp4'
    },
    # ...
]
```

## Прокси

Используются Decodo Residential прокси с geo-targeting:

| Страна | Endpoint | Port |
|--------|----------|------|
| USA | us.decodo.com | 10001 |
| UK | gb.decodo.com | 30001 |
| Germany | de.decodo.com | 20001 |

## Anti-detect Fingerprints

Генерируются автоматически по стране:
- User-Agent (Chrome Windows/Mac)
- Screen resolution
- Timezone
- Language
- WebGL renderer
- Canvas noise
- и другие параметры

## Email Verification

Автоматический парсинг кодов из:
- firstmail.ltd (основной)
- Поддержка доменов: hydrofertty.com, cryobioltty.com, и др.

## Сохранение сессий

После успешного логина cookies сохраняются в:
```
data/sessions/
├── username_cookies.pkl    # Pickle с cookies
└── username_session.json   # Метаданные сессии
```

Сессии действуют 30-90 дней. При истечении нужен re-login.

## Планировщик (TODO)

Для автоматической публикации по расписанию:
```python
# Пример с APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(upload_to_all_accounts, 'cron', hour=9)  # Каждый день в 9:00
scheduler.start()
```

## Известные ограничения

1. **Headless Chrome** может блокироваться Instagram - рекомендуется использовать GoLogin для production
2. **Rate limits** - соблюдать задержки между действиями (60-120 сек)
3. **Email verification** - firstmail.ltd может менять UI

## Troubleshooting

### "Not logged in - cookies may have expired"
Запустите re-login:
```bash
python scripts/run_automation.py --mode login-all
```

### "Could not find file input"
Instagram изменил интерфейс. Нужно обновить селекторы в `reels_uploader.py`

### "Proxy connection failed"
Проверьте:
1. Баланс на Decodo
2. Правильность credentials
3. Доступность endpoint'а

## Лицензия

Private / Internal Use Only
