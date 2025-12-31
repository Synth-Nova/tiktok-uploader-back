import { Request, Response } from "express";
import { uploadBatch, YouTubeUploadResult } from "../services/youtube.service";
import { log } from "../utils";
import * as fs from "fs";
import * as path from "path";
import AdmZip from "adm-zip";
import { v4 as uuidv4 } from "uuid";

// Тип для batch
interface BatchData {
  id: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  videosLinks: string[];
  countCompletedVideos: number;
  countFailedVideos: number;
  countTotalVideos: number;
  accountsCount: number;
  createdAt: Date;
  results: YouTubeUploadResult[];
}

// In-memory storage for batches (в продакшене использовать БД)
const batches: Map<string, BatchData> = new Map();

export async function batchUpload(req: Request, res: Response) {
  try {
    log("📥 [YouTube] Получен запрос на batch upload");

    // Проверяем файлы
    const files = req.files as { [fieldname: string]: Express.Multer.File[] };
    
    if (!files.videos || !files.accounts) {
      return res.status(400).json({
        success: false,
        error: "Требуются файлы: videos (zip) и accounts (txt)",
      });
    }

    const videosFile = files.videos[0];
    const accountsFile = files.accounts[0];
    const proxiesFile = files.proxies ? files.proxies[0] : null;

    // Получаем параметры
    const hashtag = req.body.hashtag || "";
    const description = req.body.description || "";

    // Создаем временную директорию для видео
    const tempDir = path.join(__dirname, "../../temp", uuidv4());
    fs.mkdirSync(tempDir, { recursive: true });

    // Распаковываем ZIP с видео
    log("📦 [YouTube] Распаковываем ZIP архив...");
    const zip = new AdmZip(videosFile.path);
    zip.extractAllTo(tempDir, true);

    // Находим все MP4 файлы
    const videoPaths: string[] = [];
    const findVideos = (dir: string) => {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
          findVideos(fullPath);
        } else if (item.toLowerCase().endsWith(".mp4")) {
          videoPaths.push(fullPath);
        }
      }
    };
    findVideos(tempDir);

    if (videoPaths.length === 0) {
      return res.status(400).json({
        success: false,
        error: "В ZIP архиве не найдено MP4 файлов",
      });
    }

    log(`📹 [YouTube] Найдено ${videoPaths.length} видео файлов`);

    // Читаем аккаунты
    const accountsContent = fs.readFileSync(accountsFile.path, "utf-8");
    const accounts = accountsContent
      .split("\n")
      .map(line => line.trim())
      .filter(line => line.length > 0);

    if (accounts.length === 0) {
      return res.status(400).json({
        success: false,
        error: "Файл аккаунтов пустой",
      });
    }

    log(`👥 [YouTube] Загружено ${accounts.length} аккаунтов`);

    // Читаем прокси (если есть)
    let proxies: string[] = [];
    if (proxiesFile) {
      const proxiesContent = fs.readFileSync(proxiesFile.path, "utf-8");
      proxies = proxiesContent
        .split("\n")
        .map(line => line.trim())
        .filter(line => line.length > 0);
      log(`🔌 [YouTube] Загружено ${proxies.length} прокси`);
    }

    // Создаем batch
    const batchId = uuidv4();
    const batch: BatchData = {
      id: batchId,
      status: "PROCESSING",
      videosLinks: [],
      countCompletedVideos: 0,
      countFailedVideos: 0,
      countTotalVideos: videoPaths.length,
      accountsCount: accounts.length,
      createdAt: new Date(),
      results: [],
    };
    batches.set(batchId, batch);

    // Отправляем ответ сразу
    res.json({
      success: true,
      batchId,
      message: "Загрузка начата",
    });

    // Запускаем загрузку в фоне
    (async () => {
      try {
        // Парсим теги из hashtag
        const tags = hashtag
          .split(/[,\s#]+/)
          .map((t: string) => t.trim())
          .filter((t: string) => t.length > 0);

        const results = await uploadBatch(
          videoPaths,
          accounts,
          proxies,
          "Video", // Base title
          description,
          tags,
          "public"
        );

        // Обновляем batch
        batch.results = results;
        batch.videosLinks = results
          .filter(r => r.success && r.videoUrl)
          .map(r => r.videoUrl!);
        batch.countCompletedVideos = results.filter(r => r.success).length;
        batch.countFailedVideos = results.filter(r => !r.success).length;
        batch.status = "COMPLETED";

        log(`✅ [YouTube] Batch ${batchId} завершен: ${batch.countCompletedVideos}/${batch.countTotalVideos} успешно`);
      } catch (error: any) {
        log(`❌ [YouTube] Ошибка batch ${batchId}: ${error.message}`);
        batch.status = "FAILED";
      } finally {
        // Очищаем временные файлы
        try {
          fs.rmSync(tempDir, { recursive: true, force: true });
        } catch (e) {
          // ignore
        }
      }
    })();

  } catch (error: any) {
    log(`❌ [YouTube] Ошибка batch upload: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
}

export async function getBatches(req: Request, res: Response) {
  try {
    const batchList = Array.from(batches.values()).map(batch => ({
      id: batch.id,
      status: batch.status,
      videosLinks: batch.videosLinks,
      countCompletedVideos: batch.countCompletedVideos,
      countFailedVideos: batch.countFailedVideos,
      countTotalVideos: batch.countTotalVideos,
      accountsCount: batch.accountsCount,
      createdAt: batch.createdAt,
    }));

    res.json({
      success: true,
      batches: batchList,
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
}

export async function getBatchById(req: Request, res: Response) {
  try {
    const { id } = req.params;
    const batch = batches.get(id);

    if (!batch) {
      return res.status(404).json({
        success: false,
        error: "Batch not found",
      });
    }

    res.json({
      success: true,
      batch: {
        id: batch.id,
        status: batch.status,
        videosLinks: batch.videosLinks,
        countCompletedVideos: batch.countCompletedVideos,
        countFailedVideos: batch.countFailedVideos,
        countTotalVideos: batch.countTotalVideos,
        accountsCount: batch.accountsCount,
        createdAt: batch.createdAt,
        results: batch.results,
      },
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
}
