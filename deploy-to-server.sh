#!/bin/bash

# =====================================================
# АВТОМАТИЧЕСКИЙ DEPLOYMENT FRONTEND С UNIQUIFIER
# Сервер: 217.198.12.144
# =====================================================

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DEPLOYMENT FRONTEND С VIDEO UNIQUIFIER                     ║${NC}"
echo -e "${BLUE}║   Сервер: 217.198.12.144 (Timeweb Cloud)                     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Конфигурация
SERVER="217.198.12.144"
USER="root"
PASSWORD="hF*?5AHJc#JTuF"
ARCHIVE_URL="https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz"
DEPLOY_DIR="/var/www/html"
BACKUP_DIR="/var/www/html.backup-$(date +%Y%m%d-%H%M%S)"

# Проверка sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass не установлен. Установка...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install hudochenkov/sshpass/sshpass
    elif [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        sudo apt-get update && sudo apt-get install -y sshpass
    elif [[ -f /etc/redhat-release ]]; then
        # RHEL/CentOS
        sudo yum install -y sshpass
    else
        echo -e "${YELLOW}Пожалуйста, установите sshpass вручную:${NC}"
        echo "  - macOS: brew install hudochenkov/sshpass/sshpass"
        echo "  - Ubuntu/Debian: sudo apt-get install sshpass"
        echo "  - RHEL/CentOS: sudo yum install sshpass"
        exit 1
    fi
fi

# Функция для выполнения команд на сервере
ssh_cmd() {
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" "$@"
}

echo -e "${GREEN}✓${NC} Подключение к серверу $SERVER..."

# Тест подключения
if ! ssh_cmd "echo 'Connection OK'" &> /dev/null; then
    echo -e "${YELLOW}❌ Не удалось подключиться к серверу${NC}"
    echo "Проверьте:"
    echo "  - IP адрес: $SERVER"
    echo "  - Пароль: правильный ли?"
    echo "  - Firewall: открыт ли порт 22?"
    exit 1
fi

echo -e "${GREEN}✓${NC} Подключение успешно!"
echo ""

# ШАГ 1: Скачивание архива на сервер
echo -e "${BLUE}[1/6]${NC} Скачивание production build..."
ssh_cmd "cd /tmp && wget -q --show-progress '$ARCHIVE_URL' -O frontend-build.tar.gz 2>&1 || curl -L -o frontend-build.tar.gz '$ARCHIVE_URL'"

# Проверка скачивания
if ! ssh_cmd "test -f /tmp/frontend-build.tar.gz"; then
    echo -e "${YELLOW}❌ Не удалось скачать архив${NC}"
    exit 1
fi

FILE_SIZE=$(ssh_cmd "du -h /tmp/frontend-build.tar.gz | cut -f1")
echo -e "${GREEN}✓${NC} Архив скачан (размер: $FILE_SIZE)"
echo ""

# ШАГ 2: Создание бэкапа текущей версии
echo -e "${BLUE}[2/6]${NC} Создание backup текущей версии..."
ssh_cmd "sudo cp -r $DEPLOY_DIR $BACKUP_DIR 2>/dev/null || echo 'Backup skipped (directory empty)'"
echo -e "${GREEN}✓${NC} Backup создан: $BACKUP_DIR"
echo ""

# ШАГ 3: Очистка старой версии
echo -e "${BLUE}[3/6]${NC} Очистка старой версии..."
ssh_cmd "sudo rm -rf $DEPLOY_DIR/*"
echo -e "${GREEN}✓${NC} Директория очищена"
echo ""

# ШАГ 4: Распаковка нового build
echo -e "${BLUE}[4/6]${NC} Распаковка нового frontend..."
ssh_cmd "sudo tar -xzf /tmp/frontend-build.tar.gz -C $DEPLOY_DIR/"
echo -e "${GREEN}✓${NC} Frontend распакован"
echo ""

# ШАГ 5: Настройка прав доступа
echo -e "${BLUE}[5/6]${NC} Настройка прав доступа..."
ssh_cmd "sudo chown -R www-data:www-data $DEPLOY_DIR 2>/dev/null || sudo chown -R nginx:nginx $DEPLOY_DIR"
ssh_cmd "sudo chmod -R 755 $DEPLOY_DIR"
echo -e "${GREEN}✓${NC} Права настроены"
echo ""

# ШАГ 6: Перезагрузка Nginx
echo -e "${BLUE}[6/6]${NC} Перезагрузка Nginx..."
ssh_cmd "sudo systemctl reload nginx || sudo service nginx reload"
echo -e "${GREEN}✓${NC} Nginx перезагружен"
echo ""

# Очистка временных файлов
echo -e "${BLUE}Очистка временных файлов...${NC}"
ssh_cmd "rm -f /tmp/frontend-build.tar.gz"
echo -e "${GREEN}✓${NC} Готово!"
echo ""

# ИТОГОВАЯ ИНФОРМАЦИЯ
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  🎉 DEPLOYMENT ЗАВЕРШЁН! 🎉                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Сайт доступен:${NC} https://upl.synthnova.me/"
echo -e "${BLUE}🔐 Credentials:${NC} admin / rewfdsvcx5"
echo -e "${BLUE}🎬 Uniquifier:${NC} https://upl.synthnova.me/uniquifier"
echo ""
echo -e "${YELLOW}⚠️  Важно:${NC} Очистите кеш браузера (Ctrl+Shift+R или Cmd+Shift+R)"
echo ""
echo -e "${GREEN}✓ Video Uniquifier теперь в меню!${NC}"
echo ""
