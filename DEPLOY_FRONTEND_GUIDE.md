# 🚀 DEPLOY FRONTEND С UNIQUIFIER НА СЕРВЕР

**Проблема:** Uniquifier добавлен в код (GitHub), но не задеплоен на production сервер

**Решение:** Ребилдить frontend и задеплоить на Timeweb Cloud

---

## 📋 ЧТО НУЖНО СДЕЛАТЬ

### Вариант 1: Deploy с локальной машины (Рекомендуется)

#### Шаг 1: Клонировать/обновить репозиторий
```bash
cd /home/user/webapp

# Обновить субмодули
git pull origin main
git submodule update --init --recursive

# Перейти в frontend
cd my-tiktok-uploader/frontend
git pull origin main
```

#### Шаг 2: Установить зависимости
```bash
npm install
```

#### Шаг 3: Создать production build
```bash
npm run build
```

#### Шаг 4: Создать архив для deployment
```bash
cd build
tar -czf ../frontend-build-$(date +%Y%m%d).tar.gz .
cd ..
```

#### Шаг 5: Загрузить на сервер через SCP
```bash
scp frontend-build-*.tar.gz user@217.198.12.144:/tmp/
```

#### Шаг 6: SSH на сервер и развернуть
```bash
ssh user@217.198.12.144

# Создать backup текущей версии
sudo cp -r /var/www/html /var/www/html.backup-$(date +%Y%m%d)

# Распаковать новую версию
cd /tmp
sudo tar -xzf frontend-build-*.tar.gz -C /var/www/html/

# Установить права
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Перезагрузить Nginx
sudo systemctl reload nginx

# Проверить
curl -I https://217.198.12.144/
```

---

### Вариант 2: Deploy напрямую на сервере

#### Шаг 1: SSH на сервер
```bash
ssh user@217.198.12.144
```

#### Шаг 2: Перейти в проект
```bash
cd /path/to/project/my-tiktok-uploader/frontend
# Или создать новый если нет
cd /var/www
git clone https://github.com/Synth-Nova/influence2.git frontend
cd frontend
```

#### Шаг 3: Обновить код
```bash
git pull origin main
```

#### Шаг 4: Установить Node.js (если нужно)
```bash
# Проверить версию
node -v
npm -v

# Если нет - установить
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Шаг 5: Установить зависимости
```bash
npm install
```

#### Шаг 6: Создать production build
```bash
npm run build
```

#### Шаг 7: Backup и Deploy
```bash
# Backup текущей версии
sudo cp -r /var/www/html /var/www/html.backup-$(date +%Y%m%d)

# Очистить старую версию
sudo rm -rf /var/www/html/*

# Скопировать новый build
sudo cp -r build/* /var/www/html/

# Установить права
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html
```

#### Шаг 8: Перезагрузить Nginx
```bash
sudo systemctl reload nginx
```

---

## ✅ ПРОВЕРКА DEPLOYMENT

### 1. Проверить в браузере
```
https://217.198.12.144/
```
Войти: admin / rewfdsvcx5

### 2. Проверить меню
В левом меню должна появиться ссылка:
```
🎬 Video Uniquifier
```

### 3. Проверить страницу Uniquifier
```
https://217.198.12.144/uniquifier
```

### 4. Проверить в консоли браузера
Откройте DevTools (F12) → Console
Не должно быть ошибок типа:
- "Cannot GET /uniquifier"
- "404 Not Found"

### 5. Проверить через curl
```bash
curl -s https://217.198.12.144/ | grep -i "uniquifier"
```
Должно найти упоминания uniquifier

---

## 🔍 TROUBLESHOOTING

### Проблема 1: "npm: command not found"

**Решение:**
```bash
# Установить Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

### Проблема 2: "npm install" падает с ошибками

**Решение:**
```bash
# Очистить кеш npm
npm cache clean --force

# Удалить node_modules и package-lock.json
rm -rf node_modules package-lock.json

# Переустановить
npm install
```

---

### Проблема 3: "npm run build" падает

**Решение:**
```bash
# Увеличить память для Node.js
export NODE_OPTIONS="--max-old-space-size=4096"

# Попробовать снова
npm run build
```

---

### Проблема 4: Build успешен, но Uniquifier не появился

**Причины:**
1. **Старый кеш браузера**
   - Решение: Ctrl+Shift+R (hard refresh)
   - Или: Ctrl+Shift+Delete → Очистить кеш

2. **Nginx кеширует старую версию**
   ```bash
   sudo systemctl reload nginx
   # или
   sudo nginx -s reload
   ```

3. **Build скопирован не туда**
   ```bash
   # Проверить содержимое
   ls -la /var/www/html/
   
   # Должны быть файлы:
   # index.html, static/, manifest.json и т.д.
   ```

4. **Права доступа**
   ```bash
   sudo chown -R www-data:www-data /var/www/html
   sudo chmod -R 755 /var/www/html
   ```

---

### Проблема 5: После deploy страница пустая

**Решение:**
```bash
# Проверить логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверить права
ls -la /var/www/html/

# Проверить index.html
cat /var/www/html/index.html | head -20
```

---

## 📝 ENVIRONMENT VARIABLES

Убедитесь, что `.env.production` настроен правильно:

```env
# .env.production в frontend
REACT_APP_API_URL=https://217.198.12.144/api
YOUTUBE_API_BASE_URL=http://72.56.76.237:3000
REACT_APP_UNIQUIFIER_URL=https://217.198.12.144/uniquifier
```

Если `.env.production` изменился - нужно пересобрать build:
```bash
npm run build
```

---

## 🔄 АЛЬТЕРНАТИВА: Автоматический Deploy Script

Создайте скрипт для автоматического deployment:

### deploy-frontend.sh
```bash
#!/bin/bash

echo "🚀 Starting Frontend Deployment..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Variables
PROJECT_DIR="/var/www/frontend"
BUILD_DIR="$PROJECT_DIR/build"
DEPLOY_DIR="/var/www/html"
BACKUP_DIR="/var/www/html.backup-$(date +%Y%m%d-%H%M%S)"

# Step 1: Update code
echo "📥 Pulling latest code..."
cd $PROJECT_DIR || exit 1
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Code updated${NC}"

# Step 2: Install dependencies
echo "📦 Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ npm install failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 3: Build
echo "🔨 Building production bundle..."
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Build successful${NC}"

# Step 4: Backup current version
echo "💾 Backing up current version..."
sudo cp -r $DEPLOY_DIR $BACKUP_DIR
echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"

# Step 5: Deploy
echo "🚀 Deploying new version..."
sudo rm -rf $DEPLOY_DIR/*
sudo cp -r $BUILD_DIR/* $DEPLOY_DIR/
sudo chown -R www-data:www-data $DEPLOY_DIR
sudo chmod -R 755 $DEPLOY_DIR
echo -e "${GREEN}✅ Files deployed${NC}"

# Step 6: Reload Nginx
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Nginx reload failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Nginx reloaded${NC}"

# Step 7: Verification
echo "✅ Checking deployment..."
curl -s -I https://217.198.12.144/ | head -1

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "🌐 Check: https://217.198.12.144/"
```

### Использование:
```bash
# Сделать исполняемым
chmod +x deploy-frontend.sh

# Запустить
./deploy-frontend.sh
```

---

## 📊 CHECKLIST DEPLOYMENT

- [ ] Код обновлен (git pull)
- [ ] Зависимости установлены (npm install)
- [ ] Build создан (npm run build)
- [ ] Backup сделан
- [ ] Файлы скопированы в /var/www/html
- [ ] Права установлены (www-data:www-data)
- [ ] Nginx перезагружен
- [ ] Браузер кеш очищен (Ctrl+Shift+R)
- [ ] Uniquifier появился в меню
- [ ] Страница /uniquifier открывается
- [ ] Нет ошибок в консоли браузера

---

## 🎯 КРАТКАЯ ВЕРСИЯ (TL;DR)

```bash
# На локальной машине или сервере:
cd my-tiktok-uploader/frontend
git pull origin main
npm install
npm run build

# SSH на сервер:
ssh user@217.198.12.144
sudo cp -r /var/www/html /var/www/html.backup
sudo rm -rf /var/www/html/*
sudo cp -r /path/to/build/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html
sudo systemctl reload nginx

# Проверка:
# Открыть https://217.198.12.144/
# Ctrl+Shift+R для hard refresh
# Проверить меню - должен быть Uniquifier
```

---

**Автор:** @Christiangrandcrue  
**Дата:** 2025-12-22  
**Сервер:** 217.198.12.144 (Timeweb Cloud ID 6186087)
