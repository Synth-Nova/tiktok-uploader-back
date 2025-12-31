# SynthNova Video Pipeline - Full Project Structure

## Overview

SynthNova is a multi-platform video automation system supporting TikTok, YouTube, and Instagram. The system handles video processing, account management, automated uploads, and monitoring.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SynthNova Platform                                    │
│                     https://upl.synthnova.me                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Dashboard  │    │   Pipeline   │    │   Accounts   │                  │
│  │   (React)    │    │   (HTML/JS)  │    │   Manager    │                  │
│  │   /         │     │ /pipeline.html│   │/accounts.html│                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                    │                    │                         │
│         └────────────────────┼────────────────────┘                         │
│                              │                                               │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     Backend API (Node.js/Express)                   │    │
│  │                     Port 3000 - PM2: influence-api                  │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  /api/managed-accounts/*     Account CRUD, Import, Verify, Warm    │    │
│  │  /api/darkshop/*             DarkShop Integration (balance/buy)    │    │
│  │  /api/proxies/*              Proxy Management (PX6 integration)    │    │
│  │  /api/tiktok/*               TikTok Upload Operations              │    │
│  │  /api/youtube/*              YouTube Upload Operations             │    │
│  │  /api/stats/*                Statistics and Monitoring             │    │
│  │                                                                      │    │
│  └──────────────────────────┬─────────────────────────────────────────┘    │
│                              │                                               │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │Video Editor  │    │ YouTube API  │    │   Database   │                  │
│  │Port 8081     │    │ Port 3001    │    │  PostgreSQL  │                  │
│  │(Python/Flask)│    │ Port 3002    │    │   (Prisma)   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

### Production Server: /opt/

```
/opt/
├── influence-backend/          # Main Backend (Node.js/Express/Prisma)
│   ├── src/
│   │   ├── routes/
│   │   │   ├── accounts.routes.ts      # Account Management API
│   │   │   ├── darkshop-v2.routes.ts   # DarkShop Integration
│   │   │   ├── px6.routes.ts           # PX6 Proxy Integration
│   │   │   ├── tiktok.routes.ts        # TikTok Operations
│   │   │   └── youtube.routes.ts       # YouTube Operations
│   │   ├── services/
│   │   │   ├── account-verifier.service.ts  # Multi-platform verification
│   │   │   ├── darkshop.service.ts          # DarkShop API client
│   │   │   └── warming.service.ts           # Account warming logic
│   │   └── index.ts                    # App entry point
│   ├── prisma/
│   │   └── schema.prisma               # Database schema
│   ├── package.json
│   └── ecosystem.config.js             # PM2 configuration
│
├── influence-frontend/         # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   └── Layout/
│   │   │       └── Layout.tsx          # Navigation with pipeline link
│   │   └── pages/
│   │       ├── Dashboard.tsx
│   │       ├── AccountsManager.tsx
│   │       └── ...
│   └── build/                          # Production build
│       ├── index.html                  # React SPA
│       ├── pipeline.html               # Video Pipeline UI
│       └── accounts.html               # Accounts Manager UI
│
├── video-editor/               # Video Processing (Python/Flask)
│   ├── app.py                          # Flask app entry
│   ├── api/
│   │   ├── montage_v2.py               # Video montage generation
│   │   ├── uniquifier_api.py           # Video uniquification
│   │   ├── cutter.py                   # Video cutting/trimming
│   │   └── ...
│   ├── outputs/                        # Generated videos
│   │   ├── montages/
│   │   └── uniquified/
│   └── requirements.txt
│
└── youtube-uploader/           # YouTube Upload Services
    ├── api/
    └── ...
```

### Development Sandbox: /home/user/webapp/

```
/home/user/webapp/
├── accounts-backend/           # Account Management Backend Module
│   ├── accounts.routes.ts              # API routes (20KB)
│   └── account-verifier.service.ts     # Verification service (25KB)
│
├── accounts-manager/           # Accounts Manager Frontend
│   └── accounts.html                   # Standalone UI (44KB)
│
├── video-pipeline-ui/          # Video Pipeline Frontend
│   ├── index.html                      # Main pipeline UI (107KB)
│   ├── accounts.html                   # Accounts copy
│   └── SESSION_CONTEXT.md
│
├── darkshop-v2/                # DarkShop Integration
│   ├── darkshop-v2.routes.ts
│   └── darkshop-v2.service.ts
│
├── youtube-backend/            # YouTube Upload Backend
│   └── ...
│
├── video-editor-module/        # Video Editor Module
│   ├── app.py
│   └── api/
│       ├── montage_v2.py
│       └── uniquifier_api.py
│
└── *.tar.gz                    # Deployment archives
```

---

## Database Schema (Prisma)

### ManagedAccount
```prisma
model ManagedAccount {
  id              String    @id @default(uuid())
  email           String
  password        String?
  username        String?
  backupCode      String?   // Email password for IMAP
  cookies         String?   // JSON cookies string
  platform        String    // tiktok | youtube | instagram
  type            String    // cookie | login | autoreg
  country         String    @default("US")
  status          String    @default("new")
  // Status flow: new -> verifying -> verified -> warming -> ready -> working
  // Dead states: dead | banned
  warmingProgress Float     @default(0)
  lastActionAt    DateTime?
  proxyId         String?
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}
```

### Proxy
```prisma
model Proxy {
  id          String    @id @default(uuid())
  host        String
  port        Int
  username    String?
  password    String?
  type        String    // residential | datacenter
  country     String
  provider    String    // px6 | brightdata | etc
  status      String    @default("active")
  assignedTo  String?   // Account ID
  expiresAt   DateTime?
  createdAt   DateTime  @default(now())
}
```

---

## API Endpoints

### Account Management (`/api/managed-accounts`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List accounts with filters |
| GET | `/stats` | Statistics by platform/status |
| GET | `/:id` | Get account details |
| POST | `/import` | Bulk import accounts |
| PUT | `/:id` | Update account |
| PUT | `/:id/status` | Update status |
| DELETE | `/:id` | Delete account |
| POST | `/bulk-delete` | Bulk delete |
| POST | `/bulk-status` | Bulk status update |
| POST | `/verify` | Batch verification |
| POST | `/verify/:id` | Single verification |
| POST | `/warm` | Start warming |
| GET | `/verifier/status` | Verifier capabilities |

### DarkShop (`/api/darkshop`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Balance check |
| GET | `/products` | All products |
| GET | `/products/cookies` | Cookie accounts |
| POST | `/purchase` | Buy accounts |

### Proxies (`/api/proxies`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List proxies |
| POST | `/px6/purchase` | Buy from PX6 |
| GET | `/px6/balance` | PX6 balance |

---

## Services & Ports

| Service | Port | PM2 Name | Description |
|---------|------|----------|-------------|
| Influence API | 3000 | influence-api | Main backend |
| Video Editor | 8081 | video-editor | Video processing |
| Uniquifier | 8080 | uniquifier | Video uniquification |
| YouTube API | 3001 | youtube-uploader | YouTube uploads |
| ComDev YouTube | 3002 | comdev-youtube | Additional YT |

---

## Nginx Configuration

```nginx
# Main routes
location = /pipeline.html { try_files $uri =404; }
location = /accounts.html { try_files $uri =404; }
location / { try_files $uri $uri/ /index.html; }  # React SPA

# API proxies
location /api { proxy_pass http://127.0.0.1:3000; }
location /video-editor-api { proxy_pass http://127.0.0.1:8081; }
location /uniquifier-api { proxy_pass http://127.0.0.1:8080; }
location /youtube-api/ { proxy_pass http://127.0.0.1:3001/api/; }
location /comdev-youtube-api/ { proxy_pass http://127.0.0.1:3002/api/; }

# Static files
location /video-outputs/ { alias /opt/video-editor/outputs/; }
```

---

## Deployment Commands

### Update Backend
```bash
cd /opt/influence-backend
# Download new files
wget [archive-url] -O update.tar.gz
tar -xzf update.tar.gz
# Copy files
cp [source-files] src/routes/
cp [source-files] src/services/
# Rebuild
npm run build
pm2 restart influence-api
```

### Update Frontend
```bash
cd /opt/influence-frontend/build
# Download UI files
wget [archive-url] -O ui.tar.gz
tar -xzf ui.tar.gz
cp video-pipeline-ui/pipeline.html .
cp video-pipeline-ui/accounts.html .
```

### Update Video Editor
```bash
cd /opt/video-editor
# Download new files
wget [archive-url] -O editor.tar.gz
tar -xzf editor.tar.gz
# Copy files
cp [source-files] api/
# Restart
pm2 restart video-editor
```

---

## External Integrations

### DarkShop API
- **URL**: https://dark.shopping/api/v1
- **Docs**: https://dark.shopping/developer/index
- **Features**: Account marketplace, balance, purchase

### PX6 Proxy API
- **URL**: https://px6.link/api
- **Features**: Residential proxies, purchase, management

### TikTok API (Internal)
- Upload via cookies
- Session management
- Rate limiting

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2024-12-31 | 2.0 | Account Verification V2 (TikTok/YouTube/Instagram) |
| 2024-12-30 | 1.9 | DarkShop V2, Accounts Manager UI |
| 2024-12-29 | 1.8 | Video Pipeline UI improvements |
| 2024-12-28 | 1.7 | YouTube integration, warming module |
| 2024-12-27 | 1.6 | Video Cutter V7, Studio updates |
