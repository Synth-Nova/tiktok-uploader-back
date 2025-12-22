# 🔒 SSL СЕРТИФИКАТ ДЛЯ uploader.synthnova.me

**Проблема:** DNS работает, но SSL сертификат не настроен для uploader.synthnova.me

**Статус:**
- ✅ DNS резолвится: uploader.synthnova.me → 217.198.12.144
- ✅ Сайт работает (с игнорированием SSL)
- ⚠️ SSL сертификат отсутствует для uploader.synthnova.me

---

## 🚀 БЫСТРОЕ РЕШЕНИЕ

### SSH на сервер и выполните:

```bash
# 1. Подключиться к серверу
ssh user@217.198.12.144

# 2. Получить SSL сертификат
sudo certbot --nginx -d uploader.synthnova.me

# 3. Выбрать опции:
#    - Email: [ваш email]
#    - Agree to Terms: Yes
#    - Redirect HTTP to HTTPS: Yes (2)

# 4. Проверить конфигурацию
sudo nginx -t

# 5. Перезагрузить Nginx
sudo systemctl reload nginx
```

---

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ

### Шаг 1: Подключиться к серверу
```bash
ssh user@217.198.12.144
```

### Шаг 2: Установить Certbot (если еще не установлен)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx -y
```

### Шаг 3: Получить SSL сертификат
```bash
sudo certbot --nginx -d uploader.synthnova.me
```

**Certbot спросит:**

#### 1. Email адрес:
```
Enter email address (used for urgent renewal and security notices):
```
Введите ваш email (например: admin@synthnova.me)

#### 2. Согласие с Terms of Service:
```
Please read the Terms of Service at https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf
(A)gree/(C)ancel:
```
Нажмите: **A** (Agree)

#### 3. Подписка на новости (опционально):
```
Would you be willing to share your email address with EFF?
(Y)es/(N)o:
```
Нажмите: **N** (No) - не обязательно

#### 4. Redirect HTTP to HTTPS:
```
Please choose whether or not to redirect HTTP traffic to HTTPS
1: No redirect
2: Redirect - Make all requests redirect to secure HTTPS access
Select the appropriate number [1-2]:
```
Нажмите: **2** (Redirect) - РЕКОМЕНДУЕТСЯ

### Шаг 4: Проверить установку
```bash
# Проверить конфигурацию Nginx
sudo nginx -t

# Должно вывести:
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Шаг 5: Перезагрузить Nginx
```bash
sudo systemctl reload nginx
# или
sudo service nginx reload
```

---

## ✅ ПРОВЕРКА РАБОТЫ SSL

### В браузере:
```
https://uploader.synthnova.me/
```
Должно открыться БЕЗ предупреждений о безопасности

### В командной строке:
```bash
curl -I https://uploader.synthnova.me/
```
Должно вернуть HTTP 200 или 301/302 без ошибок SSL

### Проверка сертификата:
```bash
echo | openssl s_client -servername uploader.synthnova.me -connect 217.198.12.144:443 2>/dev/null | openssl x509 -noout -dates
```
Должно показать даты действия сертификата

---

## 🔍 TROUBLESHOOTING

### Проблема 1: Certbot не может получить сертификат

**Ошибка:**
```
Failed authorization procedure. uploader.synthnova.me (http-01): 
urn:ietf:params:acme:error:unauthorized
```

**Решение:**
1. Проверьте, что DNS работает:
   ```bash
   nslookup uploader.synthnova.me
   # Должно вернуть: 217.198.12.144
   ```

2. Проверьте, что порт 80 открыт:
   ```bash
   curl -I http://uploader.synthnova.me/
   ```

3. Проверьте firewall:
   ```bash
   sudo ufw status
   # Порты 80 и 443 должны быть открыты
   ```

---

### Проблема 2: "Nginx is not running"

**Решение:**
```bash
# Запустить Nginx
sudo systemctl start nginx

# Проверить статус
sudo systemctl status nginx

# Включить автозапуск
sudo systemctl enable nginx
```

---

### Проблема 3: "Port 80 already in use"

**Решение:**
```bash
# Проверить, что использует порт 80
sudo netstat -tulpn | grep :80
# или
sudo lsof -i :80

# Если это другой процесс - остановите его
# Например, Apache:
sudo systemctl stop apache2
```

---

### Проблема 4: Сертификат получен, но сайт не открывается

**Решение:**
```bash
# Проверить логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверить конфигурацию
sudo nginx -t

# Проверить, что Nginx слушает порт 443
sudo netstat -tulpn | grep :443
```

---

## 📝 КОНФИГУРАЦИЯ NGINX (Certbot создаст автоматически)

После успешной установки SSL, Certbot создаст конфиг примерно такой:

```nginx
# /etc/nginx/sites-available/default или /etc/nginx/sites-available/uploader.synthnova.me

server {
    if ($host = uploader.synthnova.me) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name uploader.synthnova.me;
    return 404;
}

server {
    listen 443 ssl;
    server_name uploader.synthnova.me;

    ssl_certificate /etc/letsencrypt/live/uploader.synthnova.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/uploader.synthnova.me/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 🔄 АВТООБНОВЛЕНИЕ СЕРТИФИКАТА

SSL сертификаты Let's Encrypt действуют 90 дней. Certbot автоматически настраивает обновление.

### Проверка автообновления:
```bash
# Тест обновления (не обновляет реально)
sudo certbot renew --dry-run

# Должно вывести:
# Congratulations, all simulated renewals succeeded
```

### Принудительное обновление:
```bash
sudo certbot renew
```

### Проверка задачи в cron:
```bash
# Certbot добавляет задачу автоматически
sudo systemctl list-timers | grep certbot
# или
cat /etc/cron.d/certbot
```

---

## 🎯 ИТОГОВАЯ ПРОВЕРКА

После настройки SSL проверьте:

### 1. HTTP → HTTPS redirect:
```bash
curl -I http://uploader.synthnova.me/
# Должно быть: HTTP/1.1 301 Moved Permanently
# Location: https://uploader.synthnova.me/
```

### 2. HTTPS работает:
```bash
curl -I https://uploader.synthnova.me/
# Должно быть: HTTP/2 200 (или 301/302)
```

### 3. Открыть в браузере:
```
https://uploader.synthnova.me/
```
Должна быть зеленая иконка замка 🔒

### 4. Dashboard доступен:
```
https://uploader.synthnova.me/dashboard
Login: admin
Password: rewfdsvcx5
```

### 5. Uniquifier доступен:
```
https://uploader.synthnova.me/uniquifier
```

---

## 📊 СТАТУС ПОСЛЕ НАСТРОЙКИ

### До:
- ❌ http://uploader.synthnova.me/ - не работает
- ❌ https://uploader.synthnova.me/ - SSL ошибка
- ⚠️ Редирект на https://upl.synthnova.me/

### После:
- ✅ http://uploader.synthnova.me/ → автоматический redirect на HTTPS
- ✅ https://uploader.synthnova.me/ - работает с валидным SSL
- ✅ Зеленый замок в браузере 🔒
- ✅ Все страницы доступны (dashboard, uniquifier, и т.д.)

---

## 🆘 ЕСЛИ НЕ ПОЛУЧАЕТСЯ

### Вариант 1: Использовать существующий домен
Если на сервере уже настроен `upl.synthnova.me`:
```
https://upl.synthnova.me/
```

### Вариант 2: Использовать IP
```
https://217.198.12.144/
```
(но будет предупреждение о сертификате)

### Вариант 3: Обратиться за помощью
Скопируйте вывод ошибки и сообщите:
```bash
sudo certbot --nginx -d uploader.synthnova.me
# Скопируйте весь вывод
```

---

## 📞 КОНТАКТЫ

Если возникли проблемы:
1. Проверьте логи: `sudo tail -f /var/log/nginx/error.log`
2. Проверьте Certbot: `sudo certbot certificates`
3. Проверьте DNS: `nslookup uploader.synthnova.me`

---

**Автор:** @Christiangrandcrue  
**Дата:** 2025-12-22  
**Сервер:** 217.198.12.144 (Timeweb Cloud ID 6186087)
