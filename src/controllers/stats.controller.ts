import { Request, Response } from "express";
import { BatchService } from "../services/batch.service";
import prisma from "../prisma";

const batchService = new BatchService();

export class StatsController {
  async getStats(req: Request, res: Response): Promise<void> {
    try {
      const stats = await batchService.getStats();

      res.json({
        success: true,
        data: stats,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getStatsProgress(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.query;

      if (!hashtag || typeof hashtag !== "string") {
        res.status(400).json({
          success: false,
          error: "Параметр hashtag обязателен",
        });
        return;
      }

      const cleanTag = hashtag.replace("#", "").trim().toLowerCase();

      // Получаем все записи прогресса для данного хэштега
      // Сортируем по дате начала (новые сверху)
      const progressRecords = await prisma.statsProgress.findMany({
        where: {
          hashtag: cleanTag,
        },
        include: {
          account: {
            select: {
              id: true,
              sessionId: true,
              username: true,
              tiktokUid: true,
            },
          },
        },
        orderBy: {
          startedAt: "desc",
        },
        take: 100, // Ограничиваем количество записей
      });

      // Группируем по статусу для удобства
      const processing = progressRecords.filter((r) => r.status === "processing");
      const completed = progressRecords.filter((r) => r.status === "completed");
      const failed = progressRecords.filter((r) => r.status === "failed");
      const pending = progressRecords.filter((r) => r.status === "pending");

      res.json({
        success: true,
        data: {
          hashtag: cleanTag,
          summary: {
            total: progressRecords.length,
            processing: processing.length,
            completed: completed.length,
            failed: failed.length,
            pending: pending.length,
          },
          records: progressRecords.map((record) => ({
            id: record.id,
            accountId: record.accountId,
            accountSessionId: record.account.sessionId.substring(0, 12) + "...",
            username: record.username || record.account.username || "N/A",
            status: record.status,
            progress: record.progress,
            currentStep: record.currentStep,
            errorMessage: record.errorMessage,
            followers: record.followers,
            following: record.following,
            likes: record.likes,
            views: record.views,
            startedAt: record.startedAt,
            completedAt: record.completedAt,
            updatedAt: record.updatedAt,
          })),
        },
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getActiveStatsProgress(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.query;

      let whereClause: any = {
        status: {
          in: ["pending", "processing"],
        },
      };

      if (hashtag && typeof hashtag === "string") {
        const cleanTag = hashtag.replace("#", "").trim().toLowerCase();
        whereClause.hashtag = cleanTag;
      }

      // Получаем только активные задачи (в процессе или ожидающие)
      const activeRecords = await prisma.statsProgress.findMany({
        where: whereClause,
        include: {
          account: {
            select: {
              id: true,
              sessionId: true,
              username: true,
              tiktokUid: true,
            },
          },
        },
        orderBy: {
          startedAt: "desc",
        },
      });

      res.json({
        success: true,
        data: {
          total: activeRecords.length,
          records: activeRecords.map((record) => ({
            id: record.id,
            hashtag: record.hashtag,
            accountId: record.accountId,
            accountSessionId: record.account.sessionId.substring(0, 12) + "...",
            username: record.username || record.account.username || "N/A",
            status: record.status,
            progress: record.progress,
            currentStep: record.currentStep,
            followers: record.followers,
            following: record.following,
            likes: record.likes,
            views: record.views,
            startedAt: record.startedAt,
            updatedAt: record.updatedAt,
          })),
        },
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async clearOldStatsProgress(req: Request, res: Response): Promise<void> {
    try {
      // Удаляем записи старше 24 часов, которые уже завершены или провалились
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

      const deleted = await prisma.statsProgress.deleteMany({
        where: {
          AND: [
            {
              status: {
                in: ["completed", "failed"],
              },
            },
            {
              completedAt: {
                lt: oneDayAgo,
              },
            },
          ],
        },
      });

      res.json({
        success: true,
        data: {
          deleted: deleted.count,
          message: `Удалено ${deleted.count} старых записей прогресса`,
        },
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }
}

