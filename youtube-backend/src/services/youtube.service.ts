import { YouTubeUploader, YouTubeVideoConfig } from "../youtube-uploader";
import { parseCredentials, log } from "../utils";
import * as fs from "fs";
import * as path from "path";

export interface YouTubeUploadResult {
  success: boolean;
  videoUrl?: string;
  error?: string;
  accountIndex: number;
  videoFileName: string;
}

export async function uploadSingleVideo(
  videoPath: string,
  accountCredentials: string,
  proxy: string | null,
  title: string,
  description: string,
  tags: string[],
  visibility: "public" | "unlisted" | "private" = "public",
  accountIndex: number = 0
): Promise<YouTubeUploadResult> {
  let uploader: YouTubeUploader | null = null;
  const videoFileName = path.basename(videoPath);

  try {
    log(`📹 [YouTube] Начинаем загрузку видео ${videoFileName} (аккаунт ${accountIndex})`);

    // Парсим credentials
    const credentials = parseCredentials(accountCredentials);

    // Создаем uploader
    uploader = new YouTubeUploader(credentials, true, proxy || undefined);

    // Инициализируем браузер
    await uploader.initialize();

    // Авторизуемся
    await uploader.login();

    // Загружаем видео
    const videoConfig: YouTubeVideoConfig = {
      videoPath,
      title,
      description,
      tags,
      visibility,
    };

    const videoUrl = await uploader.uploadVideo(videoConfig);

    log(`✅ [YouTube] Видео ${videoFileName} успешно загружено: ${videoUrl}`);

    return {
      success: true,
      videoUrl,
      accountIndex,
      videoFileName,
    };
  } catch (error: any) {
    log(`❌ [YouTube] Ошибка загрузки видео ${videoFileName}: ${error.message}`);
    return {
      success: false,
      error: error.message,
      accountIndex,
      videoFileName,
    };
  } finally {
    if (uploader) {
      await uploader.close();
    }
  }
}

export async function uploadBatch(
  videoPaths: string[],
  accounts: string[],
  proxies: string[],
  title: string,
  description: string,
  tags: string[],
  visibility: "public" | "unlisted" | "private" = "public"
): Promise<YouTubeUploadResult[]> {
  const results: YouTubeUploadResult[] = [];

  // Распределяем видео по аккаунтам
  for (let i = 0; i < videoPaths.length; i++) {
    const videoPath = videoPaths[i];
    const accountIndex = i % accounts.length;
    const account = accounts[accountIndex];
    const proxy = proxies.length > 0 ? proxies[i % proxies.length] : null;

    // Генерируем уникальный title для каждого видео
    const videoTitle = `${title} #${i + 1}`;

    const result = await uploadSingleVideo(
      videoPath,
      account,
      proxy,
      videoTitle,
      description,
      tags,
      visibility,
      accountIndex
    );

    results.push(result);

    // Задержка между загрузками
    if (i < videoPaths.length - 1) {
      const delay = 30000 + Math.random() * 30000; // 30-60 секунд
      log(`⏳ Ожидание ${Math.round(delay / 1000)} секунд перед следующей загрузкой...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  return results;
}
