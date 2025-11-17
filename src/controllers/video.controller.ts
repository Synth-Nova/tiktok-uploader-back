import { Request, Response } from "express";
import { VideoService } from "../services/video.service";
import { VideoConfig } from "../tiktok-uploader";
import { Credentials, log, parseCookies } from "../utils";
import * as fs from "fs";

const videoService = new VideoService();
const HEADLESS = process.env.HEADLESS !== "false";

export class VideoController {
  async uploadSingle(req: Request, res: Response): Promise<void> {
    let uploadedFilePath: string | null = null;

    try {
      if (!req.file) {
        res.status(400).json({
          success: false,
          error: "Видео файл не загружен. Используйте поле 'video'",
        });
        return;
      }

      uploadedFilePath = req.file.path;
      log(`📥 Получен файл: ${req.file.originalname} (${req.file.size} bytes)`);

      const { cookies, caption, hashtags } = req.body;

      if (!cookies) {
        res.status(400).json({
          success: false,
          error: "Поле 'cookies' обязательно",
        });
        return;
      }

      if (!caption) {
        res.status(400).json({
          success: false,
          error: "Поле 'caption' обязательно",
        });
        return;
      }

      const videoUrl = await videoService.uploadSingleVideo(
        uploadedFilePath,
        cookies,
        caption,
        hashtags || "",
        HEADLESS
      );

      res.json({
        success: true,
        message: "Видео успешно загружено в TikTok",
        data: {
          originalName: req.file.originalname,
          caption: caption,
          hashtags: hashtags ? hashtags.split(",") : [],
          url: videoUrl,
        },
      });
    } catch (error: any) {
      log(`❌ Ошибка при загрузке: ${error.message}`);

      if (uploadedFilePath && fs.existsSync(uploadedFilePath)) {
        fs.unlinkSync(uploadedFilePath);
      }

      res.status(500).json({
        success: false,
        error: error.message || "Произошла ошибка при загрузке видео",
      });
    }
  }
}
