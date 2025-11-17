-- AlterTable
ALTER TABLE "video_uploads" ADD COLUMN     "accountId" TEXT;

-- CreateTable
CREATE TABLE "accounts" (
    "id" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "tiktokUid" TEXT,
    "userAgent" TEXT NOT NULL,
    "cookies" TEXT NOT NULL,
    "lastUsedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "accounts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "accounts_sessionId_key" ON "accounts"("sessionId");

-- CreateIndex
CREATE INDEX "accounts_sessionId_idx" ON "accounts"("sessionId");

-- CreateIndex
CREATE INDEX "accounts_tiktokUid_idx" ON "accounts"("tiktokUid");

-- CreateIndex
CREATE INDEX "video_uploads_accountId_idx" ON "video_uploads"("accountId");

-- AddForeignKey
ALTER TABLE "video_uploads" ADD CONSTRAINT "video_uploads_accountId_fkey" FOREIGN KEY ("accountId") REFERENCES "accounts"("id") ON DELETE SET NULL ON UPDATE CASCADE;
