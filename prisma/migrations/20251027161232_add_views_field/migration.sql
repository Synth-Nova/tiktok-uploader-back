-- AlterTable
ALTER TABLE "accounts" ADD COLUMN "views" INTEGER NOT NULL DEFAULT 0;

-- AlterTable
ALTER TABLE "account_stats" ADD COLUMN "views" INTEGER NOT NULL DEFAULT 0;

