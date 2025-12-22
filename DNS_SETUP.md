# 🌐 DNS настройки для uploader.synthnova.me

**Дата:** 2025-12-22  
**Домен:** synthnova.me  
**Субдомен:** uploader.synthnova.me  
**IP сервера:** 217.198.12.144 (Timeweb Cloud ID 6186087)

---

## 📋 DNS ЗАПИСИ - ЧТО ДОБАВИТЬ

### Вариант 1: A-запись (Рекомендуется)

```dns
Type: A
Name: uploader
Value: 217.198.12.144
TTL: 3600 (или Auto)
```

**Пояснение:**
- `Type: A` - прямая запись на IP адрес
- `Name: uploader` - субдомен (полный домен будет uploader.synthnova.me)
- `Value: 217.198.12.144` - IP вашего сервера на Timeweb
- `TTL: 3600` - время кеширования (1 час)

---

### Вариант 2: CNAME-запись (Альтернатива)

Если у вас уже есть A-запись для основного домена synthnova.me, можно использовать CNAME:

```dns
Type: CNAME
Name: uploader
Value: synthnova.me (или IP 217.198.12.144)
TTL: 3600
```

**⚠️ Рекомендую Вариант 1 (A-запись)** - он надежнее и быстрее.

---

## 🔧 ГДЕ ДОБАВИТЬ DNS ЗАПИСИ

### Если DNS у регистратора домена:

1. Войдите в панель управления доменом (где купили synthnova.me)
2. Найдите раздел **DNS Management** или **DNS Zone**
3. Добавьте новую запись:
   - **Тип:** A
   - **Хост/Имя:** uploader
   - **Значение/IP:** 217.198.12.144
   - **TTL:** 3600
4. Сохраните изменения

### Популярные регистраторы:

#### Cloudflare:
```
Dashboard → Domains → synthnova.me → DNS → Add Record
Type: A
Name: uploader
IPv4 address: 217.198.12.144
Proxy status: DNS only (серый облачок)
TTL: Auto
```

#### Namecheap:
```
Domain List → Manage → Advanced DNS → Add New Record
Type: A Record
Host: uploader
Value: 217.198.12.144
TTL: Automatic
```

#### GoDaddy:
```
My Products → Domains → synthnova.me → DNS
Type: A
Name: uploader
Value: 217.198.12.144
TTL: 1 Hour
```

#### Reg.ru / Timeweb:
```
Управление доменом → DNS настройки
Тип: A
Субдомен: uploader
IP-адрес: 217.198.12.144
TTL: 3600
```

---

## ⏱️ ВРЕМЯ ПРИМЕНЕНИЯ DNS

- **Обычно:** 5-30 минут
- **Максимум:** 24-48 часов (редко)
- **Проверка:** `nslookup uploader.synthnova.me` или `dig uploader.synthnova.me`

---

## ✅ ПРОВЕРКА DNS

### После добавления записи подождите 5-10 минут и проверьте:

#### Онлайн проверка:
- https://dns.google/query?name=uploader.synthnova.me
- https://www.whatsmydns.net/#A/uploader.synthnova.me
- https://dnschecker.org/#A/uploader.synthnova.me

#### Командная строка:
```bash
# Windows (CMD):
nslookup uploader.synthnova.me

# Linux/Mac:
dig uploader.synthnova.me
# или
host uploader.synthnova.me

# Должно вернуть:
# uploader.synthnova.me has address 217.198.12.144
```

#### Проверка в браузере:
```
http://uploader.synthnova.me
```
Должно открыть ваш проект (пока без HTTPS)

---

## 🔒 SSL СЕРТИФИКАТ (после настройки DNS)

### Шаг 1: Подключиться к серверу
```bash
ssh user@217.198.12.144
```

### Шаг 2: Установить Certbot (если еще не установлен)
```bash
# Ubuntu/Debian:
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# CentOS/RHEL:
sudo yum install certbot python3-certbot-nginx -y
```

### Шаг 3: Получить SSL сертификат
```bash
sudo certbot --nginx -d uploader.synthnova.me
```

**Certbot спросит:**
1. Email (для уведомлений): ваш email
2. Согласие с Terms of Service: Yes
3. Redirect HTTP to HTTPS: Yes (рекомендуется)

### Шаг 4: Автообновление сертификата
```bash
# Проверка автообновления:
sudo certbot renew --dry-run

# Добавить в cron (если нужно):
sudo crontab -e
# Добавить строку:
0 3 * * * certbot renew --quiet
```

---

## 📝 КОНФИГУРАЦИЯ NGINX (после SSL)

Certbot автоматически настроит Nginx, но вот как должен выглядеть конфиг:

### /etc/nginx/sites-available/uploader.synthnova.me
```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name uploader.synthnova.me;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name uploader.synthnova.me;

    # SSL сертификаты (Certbot добавит автоматически)
    ssl_certificate /etc/letsencrypt/live/uploader.synthnova.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/uploader.synthnova.me/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Frontend (React build)
    root /var/www/uploader.synthnova.me/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # TikTok API
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uniquifier API
    location /uniquifier {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Для больших файлов (видео)
        client_max_body_size 500M;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # YouTube API (если нужен)
    location /youtube-api {
        proxy_pass http://72.56.76.237:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Применить конфигурацию:
```bash
# Проверить конфиг:
sudo nginx -t

# Перезагрузить Nginx:
sudo systemctl reload nginx
```

---

## 🔄 ОБНОВЛЕНИЕ ENVIRONMENT VARIABLES

### После настройки домена обновите .env.production:

```bash
cd /home/user/webapp/my-tiktok-uploader/frontend
```

#### .env.production (обновленный):
```env
# TikTok Backend API (внутри домена через Nginx proxy)
REACT_APP_API_URL=https://uploader.synthnova.me/api

# YouTube Backend API (старый сервер)
YOUTUBE_API_BASE_URL=http://72.56.76.237:3000

# Video Uniquifier API (внутри домена через Nginx proxy)
REACT_APP_UNIQUIFIER_URL=https://uploader.synthnova.me/uniquifier
```

### Ребилд frontend:
```bash
npm install
npm run build
```

### Deploy на сервер:
```bash
# Скопировать build/ в /var/www/uploader.synthnova.me/
sudo mkdir -p /var/www/uploader.synthnova.me
sudo cp -r build/* /var/www/uploader.synthnova.me/
sudo chown -R www-data:www-data /var/www/uploader.synthnova.me
```

---

## ✅ ФИНАЛЬНАЯ ПРОВЕРКА

### После всех настроек:

1. **DNS работает:**
   ```bash
   nslookup uploader.synthnova.me
   # Должно вернуть: 217.198.12.144
   ```

2. **HTTPS работает:**
   ```
   https://uploader.synthnova.me
   ```
   Должно открыться без предупреждений о сертификате

3. **Dashboard доступен:**
   ```
   https://uploader.synthnova.me/dashboard
   Login: admin
   Password: rewfdsvcx5
   ```

4. **Uniquifier доступен:**
   ```
   https://uploader.synthnova.me/uniquifier
   ```

5. **API работает:**
   ```bash
   curl https://uploader.synthnova.me/api/health
   ```

---

## 🎯 КРАТКАЯ ИНСТРУКЦИЯ

### 1. Добавьте DNS запись:
```
Type: A
Name: uploader
Value: 217.198.12.144
TTL: 3600
```

### 2. Подождите 5-30 минут

### 3. Проверьте DNS:
```bash
nslookup uploader.synthnova.me
```

### 4. SSH на сервер:
```bash
ssh user@217.198.12.144
```

### 5. Установите SSL:
```bash
sudo certbot --nginx -d uploader.synthnova.me
```

### 6. Готово! Проверьте:
```
https://uploader.synthnova.me
```

---

## 📞 TROUBLESHOOTING

### DNS не обновился через 30 минут:
```bash
# Проверьте NS серверы домена:
dig NS synthnova.me

# Проверьте TTL:
dig uploader.synthnova.me

# Очистите кеш DNS (Windows):
ipconfig /flushdns

# Очистите кеш DNS (Mac):
sudo dscacheutil -flushcache

# Очистите кеш DNS (Linux):
sudo systemd-resolve --flush-caches
```

### SSL сертификат не работает:
```bash
# Проверьте Nginx конфиг:
sudo nginx -t

# Проверьте логи Certbot:
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Перезапустите Nginx:
sudo systemctl restart nginx
```

### Порт 80/443 заблокирован:
```bash
# Проверьте firewall:
sudo ufw status

# Откройте порты:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

---

## 📝 ПРИМЕЧАНИЯ

- **IP сервера:** 217.198.12.144 (Timeweb Cloud)
- **Старый доступ:** https://217.198.12.144/
- **Новый доступ:** https://uploader.synthnova.me/
- **Credentials остались прежними:** admin / rewfdsvcx5

После настройки домена обновите `CREDENTIALS_CHEATSHEET.md` и `PROJECT_QUICK_START.md` с новым URL!

---

**Автор:** @Christiangrandcrue  
**Дата:** 2025-12-22  
**Версия:** 1.0
