# 📋 Quick Reference - Instagram Reels Uploader

**Последнее обновление:** 2025-12-20

---

## 🚦 Статус компонентов

| Компонент | Статус | Файл | Описание |
|-----------|--------|------|----------|
| **Video Uniquifier v2.0** | ✅ Работает | `src/tools/video_uniquifier.py` | 12 методов модификации, 3 пресета |
| **Background Uniquifier v2.0** | ✅ Работает | `background_uniquifier.py` | Создание уникальных фонов для спикеров |
| **GeeLark API Client** | ⚠️ Частично | `src/integrations/geelark_api.py` | API работает, RPA зависает |
| **DuoPlus API Client** | 🔴 Заблокирован | `duoplus_integration.py` | Ошибка 160002 (нужна активация) |
| **AdsPower API Client** | ⏸️ Не тестировался | `adspower_integration.py` | Локальный антидетект браузер |
| **Text Overlay Pipeline** | ❌ Не начато | - | Наложение текста для 24 языков |
| **Mass Upload to Instagram** | ❌ Не начато | - | Загрузка 192 видео |

---

## 📂 Ключевые файлы проекта

### 🎨 Video Processing
```
instagram-reels-bot/
├── src/tools/video_uniquifier.py        ⭐ Video Uniquifier v2.0
├── background_uniquifier.py             ⭐ Background Uniquifier v2.0
├── run_uniquifier.py                    ⭐ CLI для uniquifier
└── src/tools/uniquifier_web.py          🌐 Web интерфейс (port 8080)
```

### 🔌 API Integrations
```
/home/user/webapp/
├── duoplus_integration.py               ⭐ DuoPlus Cloud Phone API
├── instagram-reels-bot/src/integrations/
│   └── geelark_api.py                   ⭐ GeeLark Cloud Phone API
└── adspower_integration.py              ⚠️ AdsPower (локальный)
```

### 🧪 Testing & Analysis
```
/home/user/webapp/
├── test_duoplus_api_v2.py               📊 27 endpoints tested
├── test_geelark_api.py                  📊 Basic API tests
└── test_upload_v2.py                    📊 Upload tests
```

### 📊 Data & Videos
```
instagram-reels-bot/data/
├── base_fixed.mp4                       ✅ Ready (2.7MB, 1920x1080)
├── test_backgrounds2/
│   ├── Маша_background.mp4              ✅ Unique (2.2MB, hue: +9.30°)
│   └── Саша_background.mp4              ✅ Unique (2.3MB, hue: +37.88°)
└── uniquified/
    └── test_unique_1.mp4                ✅ Processed (2.3MB, minimal)
```

---

## 🔧 Быстрые команды

### Video Uniquifier
```bash
cd /home/user/webapp/instagram-reels-bot

# Обработать одно видео (minimal preset)
python3 run_uniquifier.py data/base_fixed.mp4 \
    --output data/output.mp4 \
    --preset minimal

# Создать 5 уникальных версий
python3 run_uniquifier.py data/base_fixed.mp4 \
    --batch 5 \
    --output-dir ./versions \
    --preset balanced

# Запустить web интерфейс
python3 run_uniquifier.py web --port 8080
```

### Background Uniquifier
```bash
cd /home/user/webapp/instagram-reels-bot

# Создать уникальные фоны для 2 спикеров (тест)
python3 background_uniquifier.py data/base_fixed.mp4 \
    --speakers Маша Саша \
    --output-dir ./test_backgrounds2 \
    --analyze

# Создать фоны для 8 спикеров (production)
python3 background_uniquifier.py data/base_fixed.mp4 \
    --speakers Speaker1 Speaker2 Speaker3 Speaker4 Speaker5 Speaker6 Speaker7 Speaker8 \
    --output-dir ./final_backgrounds \
    --analyze
```

### API Testing
```bash
cd /home/user/webapp

# Test DuoPlus API (проверка всех endpoints)
python3 test_duoplus_api_v2.py

# Test GeeLark API
python3 test_geelark_api.py

# Test video upload
python3 test_upload_v2.py
```

---

## 🐛 Известные проблемы

### 1️⃣ DuoPlus API - Error 160002
**Симптомы:**
```json
{
  "code": 160002,
  "message": "Sorry, you do not have enough permissions to perform this operation"
}
```

**Решение:**
1. Войти: `https://my.duoplus.net/`
2. Settings → API Configuration
3. Активировать API
4. Скопировать новый ключ
5. Проверить тарифный план

---

### 2️⃣ GeeLark RPA - Tasks Hang
**Симптомы:**
```json
{
  "taskId": "597121522259202451",
  "status": "in_progress",  // Бесконечно
  "duration": "20+ checks"
}
```

**Возможные причины:**
- Неправильный формат параметров RPA задачи
- Видео не загружено в `/sdcard/DCIM/Camera/`
- API не поддерживает полностью автоматическую загрузку

**План отладки:**
1. Загрузить видео вручную на GeeLark устройство
2. Создать RPA задачу через API (только публикация)
3. Проверить, работает ли

---

### 3️⃣ Video Rotation Issue (FIXED ✅)
**Проблема:**
- `IMG_2567.mov` имеет rotation metadata (-90°)
- Background Uniquifier не учитывал ротацию
- Ошибка: "Invalid too big or non positive size for width 'X' or height 'Y'"

**Решение (применено):**
1. Исправлена ротация FFmpeg:
```bash
ffmpeg -i input.mov -vf "transpose=2" -c:a copy output.mp4
```
2. Уменьшен crop в `background_uniquifier.py` (0.3-0.8%)

---

## 📊 API Endpoints Reference

### DuoPlus API
```
Base URL: https://api.duoplus.net/api/v1
Auth: Bearer {API_KEY}

Endpoints:
POST /phone/list              # Список телефонов
POST /phone/info              # Информация о телефоне
POST /phone/power/on          # Включить
POST /phone/power/off         # Выключить
POST /file/upload             # Загрузить файл
POST /file/push               # Push file via URL
POST /rpa/task/create         # Создать RPA задачу
POST /rpa/task/list           # Список задач
GET  /rpa/task/status/{id}    # Статус задачи
```

### GeeLark API
```
Base URL: https://api.geelark.com
Auth: X-API-KEY, X-API-SECRET (headers)

Endpoints:
GET  /phone/list              # Список телефонов
POST /phone/power/on          # Включить
POST /phone/power/off         # Выключить
POST /file/upload             # Загрузить файл
POST /file/push               # Push file via URL
POST /rpa/task/instagramPubReels  # Создать задачу Instagram
GET  /rpa/task/status/{id}    # Статус задачи
```

### AdsPower API
```
Base URL: http://localhost:50325
Auth: Not required (localhost)

Endpoints:
GET  /api/v1/user/list        # Список профилей
POST /api/v1/user/create      # Создать профиль
POST /api/v1/user/update      # Обновить профиль
POST /api/v1/browser/start    # Запустить браузер
POST /api/v1/browser/stop     # Остановить браузер
```

---

## 🎬 Pipeline для 192 видео

### Scheme A: Recommended
```
1 базовое видео (IMG_2567.mov, 13MB)
    ↓
8 уникальных фонов (Background Uniquifier)
    ↓
192 видео = 8 спикеров × 24 языка (text overlay)
    ↓
192 финальных видео (Video Uniquifier, minimal)
```

### Параметры Background Uniquifier
| Speaker | Hue Shift | Brightness | Speed | Crop |
|---------|-----------|------------|-------|------|
| 1 | 0° | -0.080 | 0.960x | 0.5% |
| 2 | 45° | -0.061 | 0.970x | 1.0% |
| 3 | 90° | -0.042 | 0.980x | 1.5% |
| 4 | 135° | -0.023 | 0.990x | 2.0% |
| 5 | 180° | +0.020 | 1.010x | 2.5% |
| 6 | 225° | +0.040 | 1.020x | 3.0% |
| 7 | 270° | +0.060 | 1.030x | 0.8% |
| 8 | 315° | +0.080 | 1.040x | 1.2% |

### Video Uniquifier Presets
```python
minimal = {
    'crop': 0.3-0.5%,
    'brightness': ±0.01,
    'contrast': 0.98-1.02,
    'saturation': 0.98-1.02,
    'noise': 0.001,
    'watermark': 0.5%
}

balanced = {  # Рекомендуется для general use
    'crop': 0.5-1.5%,
    'brightness': ±0.02,
    'contrast': 0.96-1.04,
    'saturation': 0.95-1.05,
    'noise': 0.003,
    'watermark': 1%
}

aggressive = {  # Для новых аккаунтов
    'crop': 1-3%,
    'brightness': ±0.05,
    'contrast': 0.95-1.05,
    'saturation': 0.95-1.05,
    'noise': 0.005,
    'watermark': 1%
}
```

---

## 📞 Контакты API

### DuoPlus
- **Панель управления:** `https://my.duoplus.net/`
- **API документация:** `https://help.duoplus.net/docs/api-reference`
- **Beginner's Guide:** `https://help.duoplus.net/docs/sxbi0H`
- **File Upload Guide:** `https://help.duoplus.net/docs/Upload-File`

### GeeLark
- **API документация:** `https://help.geelark.com/docs/api-reference`
- **Cloud Phone Guide:** `https://help.geelark.com/docs/api`
- **RPA Manual:** `https://help.geelark.com/docs/dDIEb73N`

### AdsPower
- **API документация:** Локальная (http://localhost:50325/api/docs)
- **Требует установки:** Десктопное приложение

---

## 🎯 Next Steps

### Priority 1: Решить API проблемы
- [ ] DuoPlus: Активировать API ключ
- [ ] GeeLark: Отладить RPA tasks
- [ ] AdsPower: Протестировать (опционально)

### Priority 2: Video Pipeline
- [ ] Создать 8 финальных фоновых видео
- [ ] Автоматизировать text/watermark overlay (24 языка)
- [ ] Интегрировать финальную уникализацию (minimal)

### Priority 3: Upload & Publish
- [ ] Протестировать загрузку на cloud phone
- [ ] Протестировать публикацию Reels
- [ ] Проверить детектирование дубликатов

---

**Для полной информации см.:**
- `TECHNICAL_STRUCTURE.md` - Детальная техническая структура
- `ARCHITECTURE_DIAGRAM.md` - Визуальные диаграммы архитектуры
- `BACKGROUND_UNIQUIFIER_README.md` - Документация Background Uniquifier
