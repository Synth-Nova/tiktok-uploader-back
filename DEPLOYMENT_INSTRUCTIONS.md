# 🚀 Инструкция по Deployment Frontend с Uniquifier

## ⚡ БЫСТРЫЙ СТАРТ (для тех, кто не хочет разбираться)

### Вариант 1: Linux / macOS (через Terminal)

1. **Скачайте скрипт:**
   ```bash
   wget https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/deploy-to-server.sh
   ```

2. **Запустите:**
   ```bash
   chmod +x deploy-to-server.sh
   ./deploy-to-server.sh
   ```

3. **Готово!** Откройте https://upl.synthnova.me/ и войдите (admin / rewfdsvcx5)

---

### Вариант 2: Windows (через PowerShell или CMD)

1. **Скачайте скрипт:**
   - Откройте: https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/deploy-to-server.bat
   - Сохраните файл (Правая кнопка мыши → Сохранить как)

2. **Установите PuTTY** (если еще не установлен):
   - Скачайте: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
   - Установите полный пакет (MSI installer)

3. **Запустите:**
   - Двойной клик на `deploy-to-server.bat`
   - ИЛИ откройте CMD и выполните: `deploy-to-server.bat`

4. **Готово!** Откройте https://upl.synthnova.me/ и войдите (admin / rewfdsvcx5)

---

## 🎯 Что делает скрипт?

1. ✅ Подключается к серверу `217.198.12.144`
2. ✅ Скачивает готовый production build с GitHub
3. ✅ Создает backup старой версии
4. ✅ Разворачивает новый frontend с Uniquifier
5. ✅ Настраивает права доступа
6. ✅ Перезагружает Nginx

**Время выполнения:** ~30-60 секунд

---

## 📋 Требования

### Linux / macOS:
- `bash` (уже установлен)
- `sshpass` (скрипт установит автоматически)

### Windows:
- **PuTTY** (скачать: https://www.putty.org/)
  - Нужны файлы: `plink.exe` и `pscp.exe`

---

## 🔧 Ручной Deployment (если скрипт не работает)

### Шаг 1: Подключитесь к серверу

**Linux/macOS:**
```bash
ssh root@217.198.12.144
# Пароль: hF*?5AHJc#JTuF
```

**Windows (PuTTY):**
1. Запустите PuTTY
2. Host Name: `217.198.12.144`
3. Port: `22`
4. Connection type: `SSH`
5. Нажмите "Open"
6. Введите логин: `root`
7. Введите пароль: `hF*?5AHJc#JTuF`

---

### Шаг 2: Выполните команды на сервере

```bash
# 1. Скачать архив
cd /tmp
wget https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz

# 2. Создать backup
sudo cp -r /var/www/html /var/www/html.backup-$(date +%Y%m%d-%H%M%S)

# 3. Очистить старую версию
sudo rm -rf /var/www/html/*

# 4. Распаковать новый build
sudo tar -xzf frontend-production-20251222-042026.tar.gz -C /var/www/html/

# 5. Настроить права
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# 6. Перезагрузить Nginx
sudo systemctl reload nginx

# 7. Очистка
rm -f /tmp/frontend-production-20251222-042026.tar.gz
```

---

## ✅ Проверка после Deployment

1. **Откройте сайт:** https://upl.synthnova.me/
2. **Очистите кеш браузера:**
   - **Windows/Linux:** `Ctrl + Shift + R`
   - **macOS:** `Cmd + Shift + R`
3. **Войдите:**
   - Login: `admin`
   - Password: `rewfdsvcx5`
4. **Проверьте меню:**
   - Должен появиться пункт **"🎬 Video Uniquifier"**
5. **Откройте Uniquifier:**
   - Перейдите: https://upl.synthnova.me/uniquifier
   - Попробуйте загрузить тестовое видео

---

## 🆘 Troubleshooting (если что-то не работает)

### Проблема 1: "Connection refused" или "Permission denied"

**Решение:**
- Проверьте пароль: `hF*?5AHJc#JTuF`
- Проверьте, что сервер запущен в Timeweb Cloud
- Убедитесь, что порт 22 (SSH) открыт

---

### Проблема 2: "Uniquifier не появился в меню"

**Решение:**
1. Очистите кеш браузера (`Ctrl + Shift + R`)
2. Проверьте, что файлы развернулись:
   ```bash
   ssh root@217.198.12.144
   ls -la /var/www/html/
   ```
3. Проверьте Nginx:
   ```bash
   sudo systemctl status nginx
   sudo nginx -t
   ```

---

### Проблема 3: "sshpass not found" (Linux/macOS)

**Решение - установите sshpass:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y sshpass
```

**macOS:**
```bash
brew install hudochenkov/sshpass/sshpass
```

**RHEL/CentOS:**
```bash
sudo yum install -y sshpass
```

---

### Проблема 4: "PuTTY not found" (Windows)

**Решение:**
1. Скачайте PuTTY: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
2. Установите полный MSI пакет (включает plink.exe и pscp.exe)
3. Перезапустите CMD/PowerShell
4. Запустите скрипт снова

---

## 🔐 Credentials (для справки)

### SSH доступ к серверу:
- **Host:** 217.198.12.144
- **User:** root
- **Password:** hF*?5AHJc#JTuF

### Веб-интерфейс:
- **URL:** https://upl.synthnova.me/
- **Login:** admin
- **Password:** rewfdsvcx5

### Uniquifier:
- **URL:** https://upl.synthnova.me/uniquifier
- **Backend API:** http://217.198.12.144:8080 (требует развертывания)

---

## 📁 Файлы проекта

### На GitHub:
- **Main Repository:** https://github.com/Synth-Nova/tiktok-uploader-back
- **Frontend Submodule:** https://github.com/Synth-Nova/influence2
- **Production Build:** [frontend-production-20251222-042026.tar.gz](https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz)

### На сервере:
- **Frontend:** `/var/www/html/`
- **Nginx config:** `/etc/nginx/sites-available/default`
- **Logs:** `/var/log/nginx/`

---

## 📞 Поддержка

Если ничего не помогло:

1. **Проверьте документацию:**
   - `/home/user/webapp/PROJECT_QUICK_START.md`
   - `/home/user/webapp/CREDENTIALS_CHEATSHEET.md`
   - `/home/user/webapp/DEPLOYMENT_READY.md`

2. **Проверьте логи на сервере:**
   ```bash
   ssh root@217.198.12.144
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Свяжитесь с разработчиком** и предоставьте:
   - Текст ошибки
   - Скриншот проблемы
   - Лог-файлы

---

## ✨ После успешного Deployment

🎉 **Поздравляем!** Video Uniquifier установлен и готов к работе!

### Следующие шаги:

1. **Развернуть Python Backend** для Uniquifier (порт 8080)
2. **Протестировать загрузку видео** через UI
3. **Настроить API интеграции** (TikTok, YouTube)
4. **Активировать DuoPlus API ключ**

Подробнее в документации: `/home/user/webapp/UNIQUIFIER_INTEGRATION.md`

---

**Автоматически сгенерировано:** 2025-12-22  
**Версия:** 1.0  
**Проект:** Influence Dev (Fork ID 6186087)
