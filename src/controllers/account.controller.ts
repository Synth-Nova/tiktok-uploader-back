import { Request, Response } from "express";
import { AccountService } from "../services/account.service";

const accountService = new AccountService();

export class AccountController {
  async getAllAccounts(req: Request, res: Response): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;

      const result = await accountService.getAccountsPaginated(page, limit);

      res.json({
        success: true,
        data: result,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getAccountStats(req: Request, res: Response): Promise<void> {
    try {
      const stats = await accountService.getAccountsStats();

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

  async findAccountsByHashtag(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.query;

      if (!hashtag || typeof hashtag !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Параметр hashtag обязателен',
        });
        return;
      }

      const accounts = await accountService.findAccountsByHashtag(hashtag);

      res.json({
        success: true,
        data: {
          hashtag: hashtag,
          count: accounts.length,
          accounts: accounts,
        },
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getAllHashtags(req: Request, res: Response): Promise<void> {
    try {
      const hashtags = await accountService.getAllHashtags();

      res.json({
        success: true,
        data: hashtags,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async updateHashtagStats(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.body;

      if (!hashtag || typeof hashtag !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Параметр hashtag обязателен',
        });
        return;
      }

      const result = await accountService.updateStatsForHashtag(hashtag);

      res.json({
        success: true,
        data: result,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getHashtagStatsHistory(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.query;

      if (!hashtag || typeof hashtag !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Параметр hashtag обязателен',
        });
        return;
      }

      const history = await accountService.getStatsHistoryForHashtag(hashtag);

      res.json({
        success: true,
        data: {
          hashtag: hashtag,
          accounts: history,
        },
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async exportHashtagStatsToExcel(req: Request, res: Response): Promise<void> {
    try {
      const { hashtag } = req.query;

      if (!hashtag || typeof hashtag !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Параметр hashtag обязателен',
        });
        return;
      }

      const ExcelJS = require('exceljs');
      const history = await accountService.getStatsHistoryForHashtag(hashtag);

      if (history.length === 0) {
        res.status(404).json({
          success: false,
          error: 'Аккаунтов с этим хэштегом не найдено',
        });
        return;
      }

      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Статистика');

      // Заголовки
      worksheet.columns = [
        { header: 'Username', key: 'username', width: 20 },
        { header: 'Session ID', key: 'sessionId', width: 20 },
        { header: 'Дата создания', key: 'createdAt', width: 20 },
        { header: 'Количество видео', key: 'videosCount', width: 25 },
        { header: 'Дата измерения', key: 'date', width: 20 },
        { header: 'Подписчики', key: 'followers', width: 15 },
        { header: 'Подписки', key: 'following', width: 15 },
        { header: 'Лайки', key: 'likes', width: 15 },
        { header: 'Просмотры', key: 'views', width: 15 },
        { header: 'Источник', key: 'source', width: 25 },
      ];

      // Данные (фильтруем записи с нулевыми значениями и неизвестным username)
      // Отслеживаем username, для которых уже была добавлена инициализация
      const usernamesWithInitial = new Set<string>();

      history.forEach((account) => {
        // Пропускаем аккаунты с неизвестным username
        if (!account.username || account.username === 'N/A') {
          return;
        }

        account.statsHistory.forEach((stat: any) => {
          // Пропускаем записи где все показатели нулевые
          if (stat.followers === 0 && stat.following === 0 && stat.likes === 0 && stat.views === 0) {
            return;
          }

          // Для источника 'initial' разрешаем только одну запись на username
          if (stat.source === 'initial') {
            if (usernamesWithInitial.has(account.username)) {
              return; // Пропускаем повторную инициализацию для этого username
            }
            usernamesWithInitial.add(account.username);
          }

          worksheet.addRow({
            username: account.username,
            sessionId: account.sessionId,
            tiktokUid: account.tiktokUid || 'N/A',
            createdAt: new Date(account.createdAt).toLocaleString('ru-RU'),
            videosCount: account.videosCount,
            date: new Date(stat.date).toLocaleString('ru-RU'),
            followers: stat.followers,
            following: stat.following,
            likes: stat.likes,
            views: stat.views,
            source: stat.source === 'initial' ? 'Инициализация' : stat.source === 'manual' ? 'Ручное обновление' : 'Авто',
          });
        });
      });

      // Стилизация
      worksheet.getRow(1).font = { bold: true };
      worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE0E0E0' },
      };

      // Устанавливаем заголовки до записи
      const filename = `stats_${hashtag}_${Date.now()}.xlsx`;
      const encodedFilename = encodeURIComponent(filename);
      
      res.setHeader(
        'Content-Type',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="${encodedFilename}"; filename*=UTF-8''${encodedFilename}`
      );

      // Записываем workbook в response (write() сам вызовет res.end())
      await workbook.xlsx.write(res);
    } catch (error: any) {
      console.error('Ошибка экспорта в Excel:', error);
      // Проверяем, не был ли уже отправлен ответ
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: error.message,
        });
      }
    }
  }
}

