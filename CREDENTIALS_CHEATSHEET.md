# 🔐 ШПАРГАЛКА: ЯВКИ И ПАРОЛИ

**Быстрый доступ к credentials для обоих проектов**

---

## 🎯 ОСНОВНОЙ ПРОЕКТ (Production - ID 5788751)

### Веб-интерфейс
```
URL:      http://89.23.100.188:3000/dashboard
Login:    admin
Password: admin1
```

**⚠️ ВАЖНО:** Это PRODUCTION! НЕ ТРОГАТЬ без согласования!

---

## 🔧 ФОРК ПРОЕКТ (Development - ID 6186087)

### Веб-интерфейс
```
URL:      https://217.198.12.144/
IP:       217.198.12.144
Dashboard: https://217.198.12.144/dashboard
Login:    admin
Password: rewfdsvcx5
```

**✅ Можно менять:** Это песочница для разработки

**Примечание:** Сервер работает по IP адресу с SSL. Доменное имя не используется.

---

## 🌐 API ENDPOINTS

### Форк проект (ID 6186087)
```
TikTok API:      http://217.198.12.144:3000
YouTube API:     http://72.56.76.237:3000
Uniquifier API:  http://217.198.12.144:8080  ⚠️ НЕ ЗАПУЩЕН
```

### Основной проект (ID 5788751)
```
Main API:        http://89.23.100.188:3000
```

---

## 🐙 GITHUB REPOSITORIES

### Основной проект
```
Backend:  https://github.com/Synth-Nova/influence1
Frontend: https://github.com/Synth-Nova/influence2
```

### Форк проект
```
Wrapper:  https://github.com/Synth-Nova/tiktok-uploader-back
          (содержит influence1 и influence2 как субмодули)
```

---

## 📊 TIMEWEB CLOUD IDs

```
Основной проект:  ID 5788751
Форк проект:      ID 6186087
```

---

## 🔑 EXTERNAL APIs

### DuoPlus Cloud Phone
```
URL:       https://my.duoplus.net/
Action:    Settings → API Configuration
Status:    ⚠️ API ключ не активирован (ошибка 160002)
```

### GeeLark Cloud Phone
```
Status:    ✅ Интегрирован
Issue:     ⚠️ RPA task зависает: /rpa/task/instagramPubReels
```

---

## 🚀 БЫСТРЫЕ КОМАНДЫ

### SSH на Timeweb сервер форка
```bash
ssh user@217.198.12.144
```

### Запуск Uniquifier API
```bash
cd /path/to/instagram-reels-bot
python3 run_uniquifier.py web 8080
```

### Git workflow
```bash
cd /home/user/webapp
git status
git add .
git commit -m "feat: description"
git push origin branch-name
```

---

## 📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ

Для детальной информации читайте:
```
/home/user/webapp/PROJECT_QUICK_START.md
```

---

**Дата создания:** 2025-12-22  
**Версия:** 1.0
