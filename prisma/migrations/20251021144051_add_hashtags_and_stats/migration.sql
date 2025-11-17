-- AlterTable
ALTER TABLE "accounts" ADD COLUMN "followers" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "accounts" ADD COLUMN "following" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "accounts" ADD COLUMN "likes" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "accounts" ADD COLUMN "proxy" TEXT;

-- CreateTable
CREATE TABLE "hashtags" (
    "id" TEXT NOT NULL,
    "tag" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "hashtags_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "account_hashtags" (
    "id" TEXT NOT NULL,
    "accountId" TEXT NOT NULL,
    "hashtagId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "account_hashtags_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "hashtags_tag_key" ON "hashtags"("tag");

-- CreateIndex
CREATE INDEX "hashtags_tag_idx" ON "hashtags"("tag");

-- CreateIndex
CREATE INDEX "account_hashtags_accountId_idx" ON "account_hashtags"("accountId");

-- CreateIndex
CREATE INDEX "account_hashtags_hashtagId_idx" ON "account_hashtags"("hashtagId");

-- CreateIndex
CREATE UNIQUE INDEX "account_hashtags_accountId_hashtagId_key" ON "account_hashtags"("accountId", "hashtagId");

-- CreateTable
CREATE TABLE "account_stats" (
    "id" TEXT NOT NULL,
    "accountId" TEXT NOT NULL,
    "followers" INTEGER NOT NULL,
    "following" INTEGER NOT NULL,
    "likes" INTEGER NOT NULL,
    "source" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "account_stats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "account_stats_accountId_idx" ON "account_stats"("accountId");

-- CreateIndex
CREATE INDEX "account_stats_createdAt_idx" ON "account_stats"("createdAt");

-- AddForeignKey
ALTER TABLE "account_hashtags" ADD CONSTRAINT "account_hashtags_accountId_fkey" FOREIGN KEY ("accountId") REFERENCES "accounts"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "account_hashtags" ADD CONSTRAINT "account_hashtags_hashtagId_fkey" FOREIGN KEY ("hashtagId") REFERENCES "hashtags"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "account_stats" ADD CONSTRAINT "account_stats_accountId_fkey" FOREIGN KEY ("accountId") REFERENCES "accounts"("id") ON DELETE CASCADE ON UPDATE CASCADE;

