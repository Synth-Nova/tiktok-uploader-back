# ============================================
# TikTok Uploader - Windows Server Setup Script
# ============================================
# Этот скрипт автоматически настраивает чистый Windows Server
# для работы с TikTok Uploader
#
# Запуск: 
# 1. Откройте PowerShell от имени Администратора
# 2. Get-Content .\setup-server.ps1 -Encoding UTF8 | Set-Content .\setup-server-fixed.ps1 -Encoding UTF8
# 3. Set-ExecutionPolicy Bypass -Scope Process -Force
# 4. .\setup-server-fixed.ps1

# Обновляем PATH
#$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Ошибка: Запустите PowerShell от имени Администратора!" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Начинаем настройку сервера TikTok Uploader...`n" -ForegroundColor Green

# ============================================
# 1. Установка Chocolatey (Package Manager)
# ============================================
Write-Host "📦 Установка Chocolatey..." -ForegroundColor Yellow
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "✅ Chocolatey установлен`n" -ForegroundColor Green
} else {
    Write-Host "✅ Chocolatey уже установлен`n" -ForegroundColor Green
}

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# ============================================
# 2. Установка Node.js 22.17
# ============================================
Write-Host "📦 Установка Node.js 22.17..." -ForegroundColor Yellow
choco install nodejs --version=22.17.0 -y
Write-Host "✅ Node.js 22.17 установлен: $(node -v)`n" -ForegroundColor Green

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# ============================================
# 3. Установка Yarn
# ============================================
Write-Host "📦 Установка Yarn..." -ForegroundColor Yellow
npm install -g yarn
Write-Host "✅ Yarn установлен: $(yarn -v)`n" -ForegroundColor Green

# ============================================
# 4. Установка Google Chrome
# ============================================
Write-Host "🌐 Установка Google Chrome..." -ForegroundColor Yellow
choco install googlechrome -y
Write-Host "✅ Google Chrome установлен`n" -ForegroundColor Green

# ============================================
# 5. Установка ChromeDriver
# ============================================
Write-Host "🌐 Установка ChromeDriver..." -ForegroundColor Yellow
choco install chromedriver -y
Write-Host "✅ ChromeDriver установлен`n" -ForegroundColor Green

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# ============================================
# 6. Установка PostgreSQL 16
# ============================================
Write-Host "🐘 Установка PostgreSQL 16 (это может занять 5-10 минут)..." -ForegroundColor Yellow
choco install postgresql16 --params "/Password:M0QFNezsz601Rjtab" -y --force

Write-Host "⏳ Ожидаем запуска PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Проверяем что служба запущена
$service = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -ne 'Running') {
        Start-Service -Name "postgresql-x64-16"
        Start-Sleep -Seconds 5
    }
    Write-Host "✅ Служба PostgreSQL запущена" -ForegroundColor Green
} else {
    Write-Host "⚠️  Служба PostgreSQL не найдена, но продолжаем..." -ForegroundColor Yellow
}

# Добавляем PostgreSQL в PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "✅ PostgreSQL 16 установлен через Chocolatey`n" -ForegroundColor Green

# ============================================
# 7. Настройка базы данных PostgreSQL
# ============================================
Write-Host "🔐 Настройка базы данных PostgreSQL..." -ForegroundColor Yellow

# Находим путь к psql
$psqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (!(Test-Path $psqlPath)) {
    # Пробуем найти любую версию PostgreSQL
    $pgDirs = Get-ChildItem "C:\Program Files\PostgreSQL\" -Directory -ErrorAction SilentlyContinue
    if ($pgDirs) {
        $latestPg = $pgDirs | Sort-Object Name -Descending | Select-Object -First 1
        $psqlPath = Join-Path $latestPg.FullName "bin\psql.exe"
        Write-Host "Найден PostgreSQL: $psqlPath" -ForegroundColor Cyan
    }
}

# Устанавливаем пароль для postgres
$env:PGPASSWORD = "M0QFNezsz601Rjtab"

# Создаем SQL скрипт
$sqlScript = @"
-- Создаем пользователя
CREATE USER tiktok WITH PASSWORD 'M0QFNezsz601Rjtab';

-- Создаем базу данных
CREATE DATABASE tiktok OWNER tiktok;

-- Даем все права
GRANT ALL PRIVILEGES ON DATABASE tiktok TO tiktok;
"@

$sqlScript | Out-File -FilePath "$env:TEMP\setup-db.sql" -Encoding UTF8

# Выполняем SQL
Write-Host "Создаем пользователя и базу данных..." -ForegroundColor Cyan
& $psqlPath -U postgres -h localhost -p 5432 -f "$env:TEMP\setup-db.sql" 2>&1 | Out-Null

# Даем права на схему
$sqlSchemaScript = @"
GRANT ALL ON SCHEMA public TO tiktok;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiktok;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiktok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tiktok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tiktok;
"@

$sqlSchemaScript | Out-File -FilePath "$env:TEMP\setup-schema.sql" -Encoding UTF8
Write-Host "Настраиваем права доступа..." -ForegroundColor Cyan
& $psqlPath -U postgres -h localhost -p 5432 -d tiktok -f "$env:TEMP\setup-schema.sql" 2>&1 | Out-Null

# Очищаем переменную окружения
Remove-Item Env:\PGPASSWORD

Write-Host "✅ База данных настроена" -ForegroundColor Green
Write-Host "   Пользователь: tiktok" -ForegroundColor Cyan
Write-Host "   База данных: tiktok" -ForegroundColor Cyan
Write-Host "   Порт: 5432`n" -ForegroundColor Cyan

# ============================================
# 8. Установка Redis
# ============================================
Write-Host "📮 Установка Redis..." -ForegroundColor Yellow
choco install redis-64 -y

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "⏳ Ожидаем установки Redis..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Запускаем Redis как службу
try {
    redis-server --service-install
    redis-server --service-start
    Write-Host "✅ Redis установлен и запущен`n" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Redis установлен, но не удалось запустить как службу. Запустите вручную.`n" -ForegroundColor Yellow
}

# ============================================
# 9. Проверка текущей директории
# ============================================
Write-Host "📂 Проверка текущей директории..." -ForegroundColor Yellow

$currentPath = Get-Location
Write-Host "✅ Работаем в: $currentPath`n" -ForegroundColor Green

# Проверяем что находимся в папке проекта
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Ошибка: package.json не найден!" -ForegroundColor Red
    Write-Host "Убедитесь что запускаете скрипт из папки tiktok-uploader" -ForegroundColor Red
    exit 1
}

# ============================================
# 10. Установка зависимостей проекта
# ============================================
Write-Host "📦 Установка зависимостей проекта..." -ForegroundColor Yellow
yarn install
Write-Host "✅ Зависимости установлены`n" -ForegroundColor Green

# ============================================
# 11. Генерация Prisma Client
# ============================================
Write-Host "🔧 Генерация Prisma Client..." -ForegroundColor Yellow
yarn prisma:generate
Write-Host "✅ Prisma Client сгенерирован`n" -ForegroundColor Green

# ============================================
# 12. Применение миграций
# ============================================
Write-Host "🗄️  Применение миграций базы данных..." -ForegroundColor Yellow
yarn prisma migrate deploy
Write-Host "✅ Миграции применены`n" -ForegroundColor Green

# ============================================
# 13. Сборка проекта
# ============================================
Write-Host "🔨 Сборка проекта..." -ForegroundColor Yellow
yarn build
Write-Host "✅ Проект собран`n" -ForegroundColor Green

# ============================================
# 14. Установка PM2
# ============================================
Write-Host "📦 Установка PM2..." -ForegroundColor Yellow
npm install -g pm2
npm install -g pm2-windows-service
Write-Host "✅ PM2 установлен: $(pm2 -v)`n" -ForegroundColor Green

# ============================================
# 15. Настройка PM2 для автозапуска
# ============================================
Write-Host "⚙️  Настройка PM2 для автозапуска..." -ForegroundColor Yellow
pm2-service-install -n PM2
Write-Host "✅ PM2 настроен для автозапуска как служба Windows`n" -ForegroundColor Green

# ============================================
# 16. Запуск приложения через PM2
# ============================================
Write-Host "🚀 Запуск приложения через PM2..." -ForegroundColor Yellow
pm2 start ecosystem.config.js --only tiktok-uploader
Write-Host "✅ Приложение запущено`n" -ForegroundColor Green

# ============================================
# 17. Запуск статистики через PM2
# ============================================
Write-Host "🚀 Запуск статистики через PM2..." -ForegroundColor Yellow
pm2 start ecosystem.config.js --only tiktok-stats-worker
Write-Host "✅ Статистика запущена`n" -ForegroundColor Green

# ============================================
# 18. Запуск worker через PM2
# ============================================
Write-Host "🚀 Запуск worker через PM2..." -ForegroundColor Yellow
pm2 start ecosystem.config.js --only tiktok-worker
pm2 save
Write-Host "✅ Worker запущен`n" -ForegroundColor Green

# ============================================
# 19. Настройка правил Firewall
# ============================================
Write-Host "🔥 Настройка правил Firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "TikTok Uploader API" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
Write-Host "✅ Правило Firewall создано (порт 3000)`n" -ForegroundColor Green

# ============================================
# Финальная информация
# ============================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✨ Настройка Windows Server завершена!`n" -ForegroundColor Green

Write-Host "📊 Статус приложения:" -ForegroundColor Yellow
pm2 status

Write-Host "`n📝 Полезные команды:" -ForegroundColor Yellow
Write-Host "  pm2 status                  - статус приложений" -ForegroundColor Cyan
Write-Host "  pm2 logs tiktok-uploader    - просмотр логов" -ForegroundColor Cyan
Write-Host "  pm2 restart tiktok-uploader - перезапуск" -ForegroundColor Cyan
Write-Host "  pm2 stop tiktok-uploader    - остановка" -ForegroundColor Cyan
Write-Host "  pm2 delete tiktok-uploader  - удаление из PM2" -ForegroundColor Cyan
Write-Host "  yarn queue:clear            - очистка очереди задач" -ForegroundColor Cyan

Write-Host "`n🔗 Подключение к БД:" -ForegroundColor Yellow
Write-Host "  postgresql://tiktok:M0QFNezsz601Rjtab@localhost:5432/tiktok?schema=public" -ForegroundColor Cyan

Write-Host "`n🌐 API доступен на:" -ForegroundColor Yellow
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  http://$((Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1).IPAddress):3000" -ForegroundColor Cyan

Write-Host "`n💡 Полезная информация:" -ForegroundColor Yellow
Write-Host "  - Проект установлен в: $currentPath" -ForegroundColor Cyan
Write-Host "  - Chrome будет запускаться с GUI (настройте HEADLESS в .env)" -ForegroundColor Cyan
Write-Host "  - PM2 автоматически запустится после перезагрузки" -ForegroundColor Cyan
Write-Host "  - Логи PM2: C:\ProgramData\pm2\logs\" -ForegroundColor Cyan

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Green

Write-Host "🎉 Готово! Теперь можете загружать видео в TikTok!`n" -ForegroundColor Green
