import { Request, Response } from "express";
import { BatchService } from "../services/batch.service";
import { log } from "../utils";
import * as fs from "fs";

const batchService = new BatchService();

export class BatchController {
  async batchUpload(req: Request, res: Response): Promise<void> {
    let videosZipPath: string | null = null;
    let accountsFilePath: string | null = null;
    let proxiesFilePath: string | null = null;

    try {
      const files = req.files as { [fieldname: string]: Express.Multer.File[] };

      if (!files.videos || !files.videos[0]) {
        res.status(400).json({
          success: false,
          error: 'ZIP файл с видео не загружен. Используйте поле "videos"',
        });
        return;
      }

      if (!files.accounts || !files.accounts[0]) {
        res.status(400).json({
          success: false,
          error:
            'TXT файл с аккаунтами не загружен. Используйте поле "accounts"',
        });
        return;
      }

      if (!files.proxies || !files.proxies[0]) {
        res.status(400).json({
          success: false,
          error: 'TXT файл с прокси не загружен. Используйте поле "proxies"',
        });
        return;
      }

      videosZipPath = files.videos[0].path;
      accountsFilePath = files.accounts[0].path;
      proxiesFilePath = files.proxies[0].path;

      // Получаем хэштеги и описание из body
      const hashtags = req.body.hashtags || "";
      const description = req.body.description || "";

      const result = await batchService.createBatchUpload(
        videosZipPath,
        accountsFilePath,
        proxiesFilePath,
        hashtags,
        description
      );

      log("После создания батча в контроллере" + JSON.stringify(result));

      res.json(result);
    } catch (error: any) {
      log(`❌ Ошибка при обработке загрузки: ${error.message}`);

      // Удаляем временные файлы
      [videosZipPath, accountsFilePath, proxiesFilePath].forEach((filePath) => {
        if (filePath && fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
        }
      });

      // Определяем статус код: 400 для валидации, 500 для остального
      const isValidationError =
        error.message?.includes("не совпадает") ||
        error.message?.includes("пуст") ||
        error.message?.includes("не содержит");
      const statusCode = isValidationError ? 400 : 500;

      res.status(statusCode).json({
        success: false,
        error: error.message || "Произошла ошибка при обработке загрузки",
      });
    }
  }

  async getAllBatches(req: Request, res: Response): Promise<void> {
    try {
      const batches = await batchService.getAllBatches();

      res.json({
        success: true,
        data: batches,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  async getBatchById(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const batch = await batchService.getBatchById(id);

      if (!batch) {
        res.status(404).json({
          success: false,
          error: "Батч не найден",
        });
        return;
      }

      res.json({
        success: true,
        data: batch,
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }
}
