# 🎉 ГОТОВО! Deployment скрипты созданы

## ✅ Что сделано:

1. ✅ Созданы **автоматические скрипты** для deployment
2. ✅ Поддержка **Linux, macOS и Windows**
3. ✅ Скрипты **загружены на GitHub**
4. ✅ Подробная **инструкция** создана

---

## 🚀 КАК ЗАПУСТИТЬ DEPLOYMENT (САМЫЙ ПРОСТОЙ СПОСОБ)

### ⚡ Для Linux / macOS (1 команда):

Открой **Terminal** и выполни:

```bash
bash <(curl -s https://raw.githubusercontent.com/Synth-Nova/tiktok-uploader-back/main/deploy-to-server.sh)
```

**ВСЁ!** Скрипт сам всё сделает за 1 минуту! ⏱️

---

### ⚡ Для Windows (3 простых шага):

**Шаг 1:** Установи **PuTTY** (если еще нет):
- Скачай: https://www.putty.org/
- Установи полный пакет

**Шаг 2:** Скачай скрипт:
- Открой: https://raw.githubusercontent.com/Synth-Nova/tiktok-uploader-back/main/deploy-to-server.bat
- Нажми `Правая кнопка мыши` → `Сохранить как`
- Сохрани на рабочий стол

**Шаг 3:** Запусти скрипт:
- Двойной клик на файл `deploy-to-server.bat`

**ВСЁ!** Скрипт сам всё сделает! ⏱️

---

## 🎯 Что делает скрипт:

1. ✅ Подключается к твоему серверу `217.198.12.144`
2. ✅ Скачивает готовый production build
3. ✅ Создаёт backup старой версии (на всякий случай)
4. ✅ Разворачивает новый frontend с **Uniquifier**
5. ✅ Перезагружает Nginx

**Время работы:** 30-60 секунд

---

## 🌐 После запуска скрипта:

1. **Открой сайт:** https://upl.synthnova.me/
2. **Очисти кеш браузера:**
   - Windows/Linux: `Ctrl + Shift + R`
   - macOS: `Cmd + Shift + R`
3. **Войди:**
   - Login: `admin`
   - Password: `rewfdsvcx5`
4. **Проверь меню** — там должен появиться **"🎬 Video Uniquifier"**!

---

## 📋 Альтернатива (если скрипт не работает)

Если автоматический скрипт не работает, можешь **вручную** подключиться к серверу:

### Способ 1: Через Terminal (Linux/macOS)

```bash
ssh root@217.198.12.144
# Пароль: hF*?5AHJc#JTuF
```

Потом выполни эти команды:

```bash
cd /tmp
wget https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz
sudo cp -r /var/www/html /var/www/html.backup-$(date +%Y%m%d)
sudo rm -rf /var/www/html/*
sudo tar -xzf frontend-production-20251222-042026.tar.gz -C /var/www/html/
sudo chown -R www-data:www-data /var/www/html
sudo systemctl reload nginx
rm frontend-production-20251222-042026.tar.gz
```

### Способ 2: Через PuTTY (Windows)

1. Запусти **PuTTY**
2. В поле **Host Name** введи: `217.198.12.144`
3. Нажми **Open**
4. Введи логин: `root`
5. Введи пароль: `hF*?5AHJc#JTuF`
6. Выполни те же команды, что выше ☝️

---

## 🆘 Если что-то не работает:

### Проблема: "Connection refused"
**Решение:** Проверь, что сервер запущен в Timeweb Cloud

### Проблема: "Uniquifier не появился"
**Решение:** Очисти кеш браузера (`Ctrl + Shift + R`)

### Проблема: "sshpass not found" (Linux/macOS)
**Решение:** Установи sshpass:
- Ubuntu: `sudo apt install sshpass`
- macOS: `brew install hudochenkov/sshpass/sshpass`

### Проблема: "PuTTY not found" (Windows)
**Решение:** Скачай PuTTY с https://www.putty.org/

---

## 📁 Полезные ссылки:

- **Автоматический скрипт (Linux/macOS):** https://raw.githubusercontent.com/Synth-Nova/tiktok-uploader-back/main/deploy-to-server.sh
- **Автоматический скрипт (Windows):** https://raw.githubusercontent.com/Synth-Nova/tiktok-uploader-back/main/deploy-to-server.bat
- **Полная инструкция:** https://github.com/Synth-Nova/tiktok-uploader-back/blob/main/DEPLOYMENT_INSTRUCTIONS.md
- **Production build архив:** https://github.com/Synth-Nova/tiktok-uploader-back/raw/main/frontend-production-20251222-042026.tar.gz

---

## 🔐 Credentials (для справки):

### SSH доступ:
- Host: `217.198.12.144`
- User: `root`
- Password: `hF*?5AHJc#JTuF`

### Веб-интерфейс:
- URL: `https://upl.synthnova.me/`
- Login: `admin`
- Password: `rewfdsvcx5`

---

## ✨ Что получишь после deployment:

✅ **Video Uniquifier** в меню сайта  
✅ **Страница /uniquifier** для загрузки видео  
✅ **12 методов модификации видео** (crop, brightness, speed и т.д.)  
✅ **3 пресета** (minimal, balanced, aggressive)  
✅ **Готовый UI** с поддержкой drag-and-drop  

---

## 🎯 Следующие шаги:

После успешного deployment frontend:

1. **Разверни Python Backend** для Uniquifier (порт 8080)
2. **Протестируй загрузку** тестового видео
3. **Проверь API интеграцию** с TikTok/YouTube

Подробнее в `/home/user/webapp/UNIQUIFIER_INTEGRATION.md`

---

**🎉 Всё готово к запуску! Просто запусти скрипт и через минуту Uniquifier будет работать!**

---

**Дата:** 2025-12-22  
**Проект:** Influence Dev (Fork ID 6186087)  
**Commit:** 17ca777
