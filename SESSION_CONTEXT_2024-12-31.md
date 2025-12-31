# SynthNova Session Context - 31 December 2024

## Production Server
- **URL**: https://upl.synthnova.me
- **Backend**: /opt/influence-backend
- **Frontend**: /opt/influence-frontend/build
- **Video Editor**: /opt/video-editor

## What Was Done Today (31.12.2024)

### 1. Account Verification System V2
Implemented full account verification for 3 platforms:

**TikTok Cookie Verification:**
- `/api/passport/web/account/info/` endpoint
- `/api/user/detail/` fallback endpoint
- Returns: username, followers, following, videos, profileUrl

**YouTube Cookie Verification:**
- Checks SAPISID, SID, __Secure-1PSID cookies
- Validates session via /account page
- Returns: channelId, title, subscriberCount

**Instagram Cookie Verification:**
- Checks sessionid, ds_user_id cookies
- Validates via /accounts/edit/ endpoint
- Returns: username, followers, following, posts

**Files Created:**
- `accounts-backend/account-verifier.service.ts` - 25KB, V2 with multi-platform support
- `accounts-backend/accounts.routes.ts` - 20KB, updated routes with verifier integration

### 2. API Endpoints Added
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/managed-accounts/verify` | POST | Batch verification (ids: string[]) |
| `/api/managed-accounts/verify/:id` | POST | Single account verification |
| `/api/managed-accounts/verifier/status` | GET | Verifier status and capabilities |

### 3. Verification Results Format
```json
{
  "success": true,
  "accountId": "xxx",
  "status": "verified|dead|banned|need_verification|error",
  "platform": "tiktok|youtube|instagram",
  "type": "cookie|login",
  "details": {
    "username": "...",
    "followers": 1234,
    "videos": 56,
    "profileUrl": "https://..."
  }
}
```

## Files for Deployment

### Backend API
```bash
cd /opt/influence-backend
wget https://9999-iizrsucry9ebg87ccb608-b9b802c4.sandbox.novita.ai/accounts-backend-v2.tar.gz
tar -xzf accounts-backend-v2.tar.gz
cp accounts-backend/accounts.routes.ts src/routes/
cp accounts-backend/account-verifier.service.ts src/services/
npm run build
pm2 restart influence-api
```

### UI Files (already deployed)
- `pipeline.html` - Video Pipeline UI
- `accounts.html` - Accounts Manager

## Project Structure

```
/opt/influence-backend/
├── src/
│   ├── routes/
│   │   ├── accounts.routes.ts      # Account management API
│   │   ├── darkshop-v2.routes.ts   # DarkShop integration
│   │   └── ...
│   ├── services/
│   │   ├── account-verifier.service.ts  # Verification logic
│   │   └── ...
│   └── index.ts

/opt/influence-frontend/build/
├── index.html          # React Dashboard (SPA)
├── pipeline.html       # Video Pipeline UI
├── accounts.html       # Accounts Manager
└── static/

/opt/video-editor/
├── app.py              # Flask video editor API
├── api/
│   ├── montage_v2.py   # Montage generation
│   ├── uniquifier_api.py # Video uniquification
│   └── ...
└── outputs/            # Generated videos
```

## Active Services (PM2)
- `influence-api` - Main backend (port 3000)
- `video-editor` - Video processing (port 8081)
- `uniquifier` - Video uniquification (port 8080)
- `youtube-uploader` - YouTube API (port 3001)
- `comdev-youtube` - ComDev YouTube (port 3002)

## Database
- PostgreSQL with Prisma ORM
- Tables: ManagedAccount, Proxy, User, etc.

## Tomorrow's Tasks
1. Deploy accounts-backend-v2 to production
2. Test verification on real accounts
3. Implement account warming (Playwright automation)
4. Add WebSocket for real-time verification status

## Download URLs (valid until session ends)
- Backend V2: https://9999-iizrsucry9ebg87ccb608-b9b802c4.sandbox.novita.ai/accounts-backend-v2.tar.gz
- UI V4: https://9999-iizrsucry9ebg87ccb608-b9b802c4.sandbox.novita.ai/video-pipeline-ui-v4.tar.gz
