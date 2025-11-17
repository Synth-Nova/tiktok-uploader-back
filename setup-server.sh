#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем настройку сервера TikTok Uploader...${NC}\n"

# 1. Обновление системы
echo -e "${YELLOW}📦 Обновление системы...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Установка необходимых пакетов
echo -e "${YELLOW}📦 Установка необходимых пакетов...${NC}"
sudo apt install -y curl wget git build-essential

# 3. Установка PostgreSQL
echo -e "${YELLOW}🐘 Установка PostgreSQL...${NC}"
sudo apt install -y postgresql postgresql-contrib

# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. Создание пользователя и базы данных PostgreSQL
echo -e "${YELLOW}🔐 Настройка PostgreSQL...${NC}"

sudo -u postgres psql << EOF
-- Создаем пользователя
CREATE USER tiktok WITH PASSWORD 'M0QFNezsz601Rjtab';

-- Создаем базу данных
CREATE DATABASE tiktok OWNER tiktok;

-- Даем все права
GRANT ALL PRIVILEGES ON DATABASE tiktok TO tiktok;

-- Даем права на схему public (для PostgreSQL 15+)
\c tiktok
GRANT ALL ON SCHEMA public TO tiktok;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiktok;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiktok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tiktok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tiktok;

\q
EOF

echo -e "${GREEN}✅ PostgreSQL настроен${NC}"
echo -e "   Пользователь: tiktok"
echo -e "   База данных: tiktok"
echo -e "   Порт: 5432\n"

# 5. Установка Redis (для Bull Queue)
echo -e "${YELLOW}📮 Установка Redis...${NC}"
sudo apt install -y redis-server

# Настройка Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo -e "${GREEN}✅ Redis установлен и запущен${NC}\n"

# 6. Установка Chrome и ChromeDriver для Selenium
echo -e "${YELLOW}🌐 Установка Google Chrome и зависимостей...${NC}"

# Устанавливаем зависимости для Chrome
sudo apt install -y libxss1 libappindicator3-1 libindicator7

# Добавляем репозиторий Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Устанавливаем Chrome и ChromeDriver
sudo apt update
sudo apt install -y google-chrome-stable chromium-chromedriver

# Настройка прав для Chrome
echo -e "${YELLOW}🔐 Настройка прав для Chrome...${NC}"

# Добавляем текущего пользователя в группы для Chrome
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER

# Создаем директорию для временных файлов Chrome с правами
sudo mkdir -p /tmp/.X11-unix
sudo chmod 1777 /tmp/.X11-unix

# Устанавливаем переменные окружения для Chrome
echo "export CHROME_BIN=/usr/bin/google-chrome-stable" >> ~/.bashrc
echo "export DISPLAY=:99" >> ~/.bashrc

echo -e "${GREEN}✅ Google Chrome и ChromeDriver установлены${NC}\n"

# 7. Установка NVM
echo -e "${YELLOW}📦 Установка NVM...${NC}"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash

# Загружаем NVM в текущую сессию
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo -e "${GREEN}✅ NVM установлен${NC}\n"

# 8. Установка Node.js 22.17
echo -e "${YELLOW}📦 Установка Node.js 22.17...${NC}"
nvm install 22.17
nvm use 22.17
nvm alias default 22.17

echo -e "${GREEN}✅ Node.js установлен: $(node -v)${NC}\n"

# 9. Установка Yarn и PM2
echo -e "${YELLOW}📦 Установка Yarn и PM2...${NC}"
npm install -g yarn pm2

echo -e "${GREEN}✅ Yarn установлен: $(yarn -v)${NC}"
echo -e "${GREEN}✅ PM2 установлен: $(pm2 -v)${NC}\n"

# 10. Настройка PM2 для автозапуска
echo -e "${YELLOW}⚙️  Настройка PM2 для автозапуска...${NC}"
pm2 startup systemd -u $USER --hp $HOME
sudo env PATH=$PATH:/home/$USER/.nvm/versions/node/$(node -v)/bin pm2 startup systemd -u $USER --hp $HOME

echo -e "${GREEN}✅ PM2 настроен для автозапуска${NC}\n"

# 12. Установка зависимостей Node.js проекта
echo -e "${YELLOW}📦 Установка зависимостей проекта...${NC}"
yarn install

echo -e "${GREEN}✅ Зависимости установлены${NC}\n"

# 13. Генерация Prisma Client
echo -e "${YELLOW}🔧 Генерация Prisma Client...${NC}"
yarn prisma:generate

echo -e "${GREEN}✅ Prisma Client сгенерирован${NC}\n"

# 14. Применение миграций
echo -e "${YELLOW}🗄️  Применение миграций базы данных...${NC}"
yarn prisma migrate deploy

echo -e "${GREEN}✅ Миграции применены${NC}\n"

# 15. Сборка проекта
echo -e "${YELLOW}🔨 Сборка проекта...${NC}"
yarn build

echo -e "${GREEN}✅ Проект собран${NC}\n"

# 16. Запуск через PM2
echo -e "${YELLOW}🚀 Запуск приложения через PM2...${NC}"
pm2 start yarn --name "tiktok-uploader" -- start
pm2 save

echo -e "${GREEN}✅ Приложение запущено${NC}\n"

# 17. Информация о статусе
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Настройка сервера завершена!${NC}\n"

echo -e "${YELLOW}📊 Статус приложения:${NC}"
pm2 status

echo -e "\n${YELLOW}📝 Полезные команды:${NC}"
echo -e "  pm2 status              - статус приложений"
echo -e "  pm2 logs tiktok-uploader - просмотр логов"
echo -e "  pm2 restart tiktok-uploader - перезапуск"
echo -e "  pm2 stop tiktok-uploader - остановка"
echo -e "  pm2 delete tiktok-uploader - удаление из PM2"
echo -e "  yarn queue:clear        - очистка очереди задач"

echo -e "\n${YELLOW}🔗 Подключение к БД:${NC}"
echo -e "  postgresql://tiktok:M0QFNezsz601Rjtab@localhost:5432/tiktok?schema=public"

echo -e "\n${YELLOW}🌐 API доступен на:${NC}"
echo -e "  http://localhost:3000"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

