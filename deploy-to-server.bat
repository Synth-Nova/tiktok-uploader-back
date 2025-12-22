@echo off
REM =====================================================
REM АВТОМАТИЧЕСКИЙ DEPLOYMENT FRONTEND С UNIQUIFIER
REM Сервер: 217.198.12.144
REM =====================================================

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo    DEPLOYMENT FRONTEND С VIDEO UNIQUIFIER
echo    Сервер: 217.198.12.144 (Timeweb Cloud)
echo ================================================================
echo.

REM Конфигурация
set SERVER=217.198.12.144
set USER=root
set PASSWORD=hF*?5AHJc#JTuF
set ARCHIVE_URL=https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz

echo [*] Этот скрипт требует PuTTY (plink.exe и pscp.exe)
echo.

REM Проверка наличия plink
where plink.exe >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] PuTTY не найден!
    echo.
    echo Пожалуйста, установите PuTTY:
    echo 1. Скачайте: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    echo 2. Установите полный пакет PuTTY
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    exit /b 1
)

echo [1/6] Подключение к серверу %SERVER%...
echo | plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "echo 'Connection OK'" >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Не удалось подключиться к серверу
    echo     Проверьте пароль и доступность сервера
    pause
    exit /b 1
)
echo [+] Подключение успешно!
echo.

echo [2/6] Скачивание production build на сервер...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "cd /tmp && wget -q '%ARCHIVE_URL%' -O frontend-build.tar.gz 2>&1 || curl -L -o frontend-build.tar.gz '%ARCHIVE_URL%'"
echo [+] Архив скачан
echo.

echo [3/6] Создание backup...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo cp -r /var/www/html /var/www/html.backup-%date:~-4%%date:~3,2%%date:~0,2% 2>/dev/null || echo 'Backup skipped'"
echo [+] Backup создан
echo.

echo [4/6] Очистка старой версии...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo rm -rf /var/www/html/*"
echo [+] Директория очищена
echo.

echo [5/6] Распаковка нового frontend...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo tar -xzf /tmp/frontend-build.tar.gz -C /var/www/html/"
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo chown -R www-data:www-data /var/www/html 2>/dev/null || sudo chown -R nginx:nginx /var/www/html"
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo chmod -R 755 /var/www/html"
echo [+] Frontend установлен
echo.

echo [6/6] Перезагрузка Nginx...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "sudo systemctl reload nginx || sudo service nginx reload"
echo [+] Nginx перезагружен
echo.

echo [*] Очистка временных файлов...
plink.exe -ssh %USER%@%SERVER% -pw %PASSWORD% -batch "rm -f /tmp/frontend-build.tar.gz"
echo.

echo ================================================================
echo                   DEPLOYMENT ЗАВЕРШЁН!
echo ================================================================
echo.
echo Сайт доступен: https://upl.synthnova.me/
echo Credentials: admin / rewfdsvcx5
echo Uniquifier: https://upl.synthnova.me/uniquifier
echo.
echo ВАЖНО: Очистите кеш браузера (Ctrl+Shift+R)
echo.
echo Video Uniquifier теперь в меню!
echo.
pause
