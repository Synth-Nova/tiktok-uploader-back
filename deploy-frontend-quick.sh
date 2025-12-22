#!/bin/bash

# 🚀 СКРИПТ БЫСТРОГО DEPLOYMENT FRONTEND
# Для сервера: 217.198.12.144 (upl.synthnova.me)
# Что делает: Деплоит frontend с Uniquifier на production

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║         🚀 FRONTEND DEPLOYMENT - UNIQUIFIER                       ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
GITHUB_REPO="https://github.com/Synth-Nova/influence2.git"
WORK_DIR="/tmp/frontend-build-$(date +%Y%m%d-%H%M%S)"
DEPLOY_DIR="/var/www/html"
BACKUP_DIR="/var/www/html.backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   GitHub Repo: $GITHUB_REPO"
echo "   Work Dir: $WORK_DIR"
echo "   Deploy Dir: $DEPLOY_DIR"
echo "   Backup Dir: $BACKUP_DIR"
echo ""

# Step 1: Clone repository
echo -e "${YELLOW}📥 Step 1/7: Cloning repository...${NC}"
git clone --depth 1 $GITHUB_REPO $WORK_DIR
cd $WORK_DIR
echo -e "${GREEN}✅ Repository cloned${NC}"
echo ""

# Step 2: Check Node.js
echo -e "${YELLOW}🔍 Step 2/7: Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found! Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo "   Node version: $(node -v)"
echo "   NPM version: $(npm -v)"
echo -e "${GREEN}✅ Node.js ready${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}📦 Step 3/7: Installing dependencies...${NC}"
npm install --legacy-peer-deps
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Build production bundle
echo -e "${YELLOW}🔨 Step 4/7: Building production bundle...${NC}"
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
echo -e "${GREEN}✅ Build successful${NC}"
echo ""

# Step 5: Backup current version
echo -e "${YELLOW}💾 Step 5/7: Backing up current version...${NC}"
if [ -d "$DEPLOY_DIR" ]; then
    sudo cp -r $DEPLOY_DIR $BACKUP_DIR
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}⚠️  No existing deployment to backup${NC}"
fi
echo ""

# Step 6: Deploy new version
echo -e "${YELLOW}🚀 Step 6/7: Deploying new version...${NC}"
sudo rm -rf $DEPLOY_DIR/*
sudo cp -r $WORK_DIR/build/* $DEPLOY_DIR/
sudo chown -R www-data:www-data $DEPLOY_DIR
sudo chmod -R 755 $DEPLOY_DIR
echo -e "${GREEN}✅ New version deployed${NC}"
echo ""

# Step 7: Reload Nginx
echo -e "${YELLOW}🔄 Step 7/7: Reloading Nginx...${NC}"
sudo systemctl reload nginx
echo -e "${GREEN}✅ Nginx reloaded${NC}"
echo ""

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
cd /
rm -rf $WORK_DIR
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Verification
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║              🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉            ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Frontend deployed with Uniquifier!${NC}"
echo ""
echo "🌐 Access your application:"
echo "   https://upl.synthnova.me/"
echo "   https://217.198.12.144/"
echo ""
echo "🔐 Login credentials:"
echo "   Username: admin"
echo "   Password: rewfdsvcx5"
echo ""
echo "📝 Next steps:"
echo "   1. Open https://upl.synthnova.me/ in browser"
echo "   2. Press Ctrl+Shift+R to hard refresh (clear cache)"
echo "   3. Login and check the menu"
echo "   4. You should see: 🎬 Video Uniquifier"
echo ""
echo -e "${YELLOW}⚠️  Remember to clear browser cache (Ctrl+Shift+R)${NC}"
