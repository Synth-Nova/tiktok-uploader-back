# =====================================================
# АВТОМАТИЧЕСКИЙ DEPLOYMENT FRONTEND С UNIQUIFIER
# Сервер: 217.198.12.144
# PowerShell версия
# =====================================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   DEPLOYMENT FRONTEND С VIDEO UNIQUIFIER                     ║" -ForegroundColor Cyan
Write-Host "║   Сервер: 217.198.12.144 (Timeweb Cloud)                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Конфигурация
$SERVER = "217.198.12.144"
$USER = "root"
$PASSWORD = "hF*?5AHJc#JTuF"
$ARCHIVE_URL = "https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz"

# Проверка наличия ssh
$sshExists = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshExists) {
    Write-Host "[!] SSH не найден!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Пожалуйста, установите OpenSSH:" -ForegroundColor Yellow
    Write-Host "1. Откройте 'Параметры Windows' (Win+I)" -ForegroundColor Yellow
    Write-Host "2. Перейдите: Приложения → Дополнительные компоненты" -ForegroundColor Yellow
    Write-Host "3. Найдите и установите 'Клиент OpenSSH'" -ForegroundColor Yellow
    Write-Host "4. Перезапустите PowerShell" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "[*] Подготовка deployment..." -ForegroundColor Green
Write-Host ""

# Создание команд для выполнения на сервере
$commands = @"
cd /tmp && \
wget -q https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz -O frontend-build.tar.gz 2>&1 || curl -L -o frontend-build.tar.gz https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz && \
echo '[1/6] Архив скачан' && \
sudo cp -r /var/www/html /var/www/html.backup-`$(date +%Y%m%d-%H%M%S) 2>/dev/null && \
echo '[2/6] Backup создан' && \
sudo rm -rf /var/www/html/* && \
echo '[3/6] Старая версия удалена' && \
sudo tar -xzf frontend-build.tar.gz -C /var/www/html/ && \
echo '[4/6] Новый frontend распакован' && \
sudo chown -R www-data:www-data /var/www/html 2>/dev/null || sudo chown -R nginx:nginx /var/www/html && \
sudo chmod -R 755 /var/www/html && \
echo '[5/6] Права настроены' && \
sudo systemctl reload nginx || sudo service nginx reload && \
echo '[6/6] Nginx перезагружен' && \
rm -f frontend-build.tar.gz && \
echo '' && \
echo '╔═══════════════════════════════════════════════════════════════╗' && \
echo '║              🎉 DEPLOYMENT ЗАВЕРШЁН! 🎉                      ║' && \
echo '╚═══════════════════════════════════════════════════════════════╝' && \
echo '' && \
echo '📍 Сайт: https://upl.synthnova.me/' && \
echo '🔐 Login: admin / rewfdsvcx5' && \
echo '🎬 Uniquifier: https://upl.synthnova.me/uniquifier' && \
echo '' && \
echo '⚠️  Очистите кеш браузера (Ctrl+Shift+R)' && \
echo ''
"@

Write-Host "[*] Подключение к серверу $SERVER..." -ForegroundColor Green
Write-Host "[*] Пароль будет передан автоматически" -ForegroundColor Yellow
Write-Host ""

# Создание временного файла с паролем для sshpass (если доступен)
# Если sshpass недоступен, используем SSH с паролем через stdin
try {
    # Попытка использовать plink (если установлен PuTTY)
    $plinkExists = Get-Command plink -ErrorAction SilentlyContinue
    if ($plinkExists) {
        Write-Host "[*] Используется PuTTY plink для подключения..." -ForegroundColor Cyan
        echo y | plink -ssh "$USER@$SERVER" -pw "$PASSWORD" -batch "$commands"
    } else {
        # Использование стандартного SSH (потребуется ввод пароля вручную)
        Write-Host "[!] ВНИМАНИЕ: Потребуется ввод пароля вручную" -ForegroundColor Yellow
        Write-Host "[*] Пароль: $PASSWORD" -ForegroundColor Green
        Write-Host ""
        Write-Host "Скопируйте пароль выше и вставьте при запросе" -ForegroundColor Yellow
        Write-Host "(Пароль при вводе НЕ ОТОБРАЖАЕТСЯ - это нормально)" -ForegroundColor Yellow
        Write-Host ""
        
        ssh "$USER@$SERVER" "$commands"
    }
    
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║              ✅ DEPLOYMENT ЗАВЕРШЁН УСПЕШНО! ✅              ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Сайт доступен:  https://upl.synthnova.me/" -ForegroundColor Cyan
    Write-Host "🔐 Credentials:    admin / rewfdsvcx5" -ForegroundColor Cyan
    Write-Host "🎬 Uniquifier:     https://upl.synthnova.me/uniquifier" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  ВАЖНО: Очистите кеш браузера (Ctrl+Shift+R)" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "[!] Ошибка при выполнении deployment:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
}

Write-Host "Нажмите Enter для выхода..."
Read-Host
