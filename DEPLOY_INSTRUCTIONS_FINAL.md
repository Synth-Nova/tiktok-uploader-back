# 🚀 Финальная инструкция по деплою превью (исправлена)

## ❗ Что исправлено:
- ✅ Бэкенд теперь копирует файлы в `/opt/video-editor/outputs/` с префиксом `preview_`
- ✅ Превью доступны через существующий Nginx endpoint: `/video-outputs/`
- ✅ Фронтенд использует `preview_url` напрямую: `https://upl.synthnova.me/video-outputs/preview_temp_0_video.mp4`
- ✅ Не нужен новый endpoint - работает через готовую инфраструктуру!

---

## 📦 Файлы для деплоя:

**Скачайте из sandbox:**
- `/tmp/frontend-preview-v2.tar.gz` (558 KB)
- `/tmp/backend-preview-v2.tar.gz` (13 KB)

---

## 🔧 Команды для деплоя на сервере 217.198.12.144:

### Вариант 1: Через SSH (один блок)

```bash
ssh root@217.198.12.144 << 'DEPLOY_SCRIPT'

# 1. Деплой фронтенда
echo "📂 Деплой фронтенда..."
cd /opt/influence-frontend
rm -rf build_backup
[ -d "build" ] && mv build build_backup
mkdir -p build
tar -xzf /tmp/frontend-preview-v2.tar.gz -C build/

# 2. Деплой бэкенда
echo "📂 Деплой бэкенда..."
cd /opt
[ -d "video-editor" ] && cp -r video-editor video-editor-backup
tar -xzf /tmp/backend-preview-v2.tar.gz -C /opt/
rm -rf video-editor
mv video-editor-module video-editor

# 3. Перезапуск сервисов
echo "🔄 Перезапуск PM2..."
pm2 restart video-editor-api

echo "🔄 Перезагрузка Nginx..."
nginx -t && systemctl reload nginx

echo "✅ Деплой завершен!"
pm2 status video-editor-api

DEPLOY_SCRIPT
```

### Вариант 2: Пошаговый

```bash
# Шаг 1: Подключение
ssh root@217.198.12.144

# Шаг 2: Загрузка архивов (если еще не загружены)
# Загрузите файлы в /tmp/ на сервере

# Шаг 3: Фронтенд
cd /opt/influence-frontend
rm -rf build_backup
mv build build_backup 2>/dev/null || true
mkdir -p build
tar -xzf /tmp/frontend-preview-v2.tar.gz -C build/

# Шаг 4: Бэкенд
cd /opt
tar -xzf /tmp/backend-preview-v2.tar.gz -C /opt/
rm -rf video-editor
mv video-editor-module video-editor

# Шаг 5: Перезапуск
pm2 restart video-editor-api
nginx -t && systemctl reload nginx
pm2 status
```

---

## 🎯 Что изменилось в коде:

### Backend (montage_v2.py):
```python
# При анализе копируем файл в outputs/
output_preview_path = os.path.join(output_folder, f'preview_{filename}')
shutil.copy2(filepath, output_preview_path)

# Добавляем preview_url в ответ
analyzed_shots.append({
    'index': idx,
    'original_filename': shot.filename,
    'duration': round(info['duration'], 2),
    'width': info['width'],
    'height': info['height'],
    'fps': round(info['fps'], 2),
    'temp_path': filename,
    'preview_url': f'/video-outputs/preview_{filename}'  # ← Новое поле!
})
```

### Frontend (VideoEditorV2.tsx):
```tsx
{shot.preview_url && (
  <div className="shot-preview">
    <video 
      src={`https://upl.synthnova.me${shot.preview_url}`}
      preload="metadata"
      muted
      onLoadedMetadata={(e) => {
        const video = e.currentTarget;
        video.currentTime = Math.min(0.5, shot.duration / 2);
      }}
      onError={(e) => {
        console.error('Failed to load preview:', shot.preview_url);
      }}
    />
  </div>
)}
```

---

## 🧪 Проверка после деплоя:

1. Откройте: **https://upl.synthnova.me/video-editor-v2**
2. Очистите кэш: **Ctrl + Shift + R**
3. Войдите: `admin` / `rewfdsvcx5`
4. Загрузите **3+ видео**
5. Нажмите **"🔍 Анализировать Шоты"**
6. **Превью должны появиться слева от каждого шота!** 🎬

---

## 🔍 Проверка в браузере (F12):

Если превью не работает, откройте консоль (F12) и проверьте:

```javascript
// Должны видеть запросы к:
https://upl.synthnova.me/video-outputs/preview_temp_0_yourfile.mp4
https://upl.synthnova.me/video-outputs/preview_temp_1_yourfile.mp4
...

// Если 404 - проверьте, что файлы скопированы:
ssh root@217.198.12.144 "ls -lh /opt/video-editor/outputs/preview_*"
```

---

## 🐛 Troubleshooting:

### Проблема 1: "Failed to load preview"
**Решение:**
```bash
# На сервере проверьте права доступа:
ssh root@217.198.12.144
ls -la /opt/video-editor/outputs/
chmod 755 /opt/video-editor/outputs/
chmod 644 /opt/video-editor/outputs/preview_*
```

### Проблема 2: Превью не показываются
**Решение:**
```bash
# Проверьте, что PM2 перезапущен:
pm2 restart video-editor-api
pm2 logs video-editor-api --lines 50
```

### Проблема 3: 403 Forbidden
**Решение:**
```bash
# Проверьте Nginx конфигурацию:
nginx -t
cat /etc/nginx/sites-available/influence | grep video-outputs
systemctl reload nginx
```

---

## 📊 Ожидаемый результат:

```
╔═══════════════════════════════════════════════════════╗
║  🎯 Hook - my_video.mp4                               ║
║  ┌───────────┐  📐 1920x1080 @ 30.0fps               ║
║  │ [ВИДЕО]   │  ⏱️ Длительность: 8.45 сек             ║
║  │ ПРЕВЬЮ    │                                         ║
║  │ (КАДР)    │  [Тип: Hook ▼] [Начало: 0.0s]         ║
║  │           │  [Конец: 8.45s] [✓] Случайное смещение ║
║  └───────────┘                                         ║
╚═══════════════════════════════════════════════════════╝
```

---

## ✅ После успешного деплоя:

Напишите мне, если всё работает, или пришлите скриншот с ошибкой из консоли (F12) если что-то не так!

