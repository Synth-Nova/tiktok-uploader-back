-- CreateTable
CREATE TABLE "stats_progress" (
    "id" TEXT NOT NULL,
    "hashtag" TEXT NOT NULL,
    "accountId" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "progress" INTEGER NOT NULL DEFAULT 0,
    "currentStep" TEXT,
    "errorMessage" TEXT,
    "followers" INTEGER,
    "following" INTEGER,
    "likes" INTEGER,
    "views" INTEGER,
    "username" TEXT,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" TIMESTAMP(3),
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "stats_progress_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "stats_progress_hashtag_idx" ON "stats_progress"("hashtag");

-- CreateIndex
CREATE INDEX "stats_progress_accountId_idx" ON "stats_progress"("accountId");

-- CreateIndex
CREATE INDEX "stats_progress_status_idx" ON "stats_progress"("status");

-- CreateIndex
CREATE INDEX "stats_progress_startedAt_idx" ON "stats_progress"("startedAt");

-- AddForeignKey
ALTER TABLE "stats_progress" ADD CONSTRAINT "stats_progress_accountId_fkey" FOREIGN KEY ("accountId") REFERENCES "accounts"("id") ON DELETE CASCADE ON UPDATE CASCADE;

