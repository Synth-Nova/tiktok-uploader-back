import { Job } from "bull";
import { uploadQueue, UploadJobData } from "../queues/upload.queue";
import prisma from "../prisma";
import { log, parseCookies } from "../utils";
import * as fs from "fs";
import { TikTokUploader } from "../tiktok-uploader";
import { incrementProcessedVideos } from "../utils/chrome-cleanup";

const HEADLESS = process.env.HEADLESS !== "false";

async function processUploadJob(job: Job<UploadJobData>): Promise<void> {
  const {
    batchId,
    videoId,
    videoPath,
    accountCookie,
    accountIndex,
    proxy,
    caption,
    hashtags,
    scheduledAt,
    userAgent,
    deleteExistingVideos,
  } = job.data;

  log(
    `🚀 Worker: начинаем загрузку видео ${videoId} (аккаунт ${accountIndex}) запланировано на ${scheduledAt}, UA: ${userAgent.substring(
      0,
      40
    )}...`
  );

  if (deleteExistingVideos) {
    log(`🗑️ Worker: новый аккаунт, будут удалены существующие видео`);
  }

  try {
    await prisma.videoUpload.update({
      where: { id: videoId },
      data: { status: "uploading" },
    });

    log(`📹 Worker: загрузка видео ${videoId}: ${videoPath}`);

    let parsedCookies;
    try {
      const parsed = JSON.parse(accountCookie);
      if (Array.isArray(parsed)) {
        parsedCookies = parseCookies(accountCookie);
      } else {
        parsedCookies = parsed;
      }
    } catch (e) {
      parsedCookies = parseCookies(accountCookie);
    }

    const uploader = new TikTokUploader(
      {
        username: "",
        password: "",
        email: "",
        email_password: "",
        cookies_string: "",
        cookies: parsedCookies,
      },
      HEADLESS,
      proxy,
      userAgent || undefined
    );

    let videoUrl = "";
    try {
      await uploader.initialize();

      await uploader.login();

      // Удаляем существующие видео для новых аккаунтов
      if (deleteExistingVideos) {
        try {
          log(
            `🗑️ Worker: начинаем удаление существующих видео для нового аккаунта ${accountIndex}`
          );
          const deletedCount = await uploader.deleteAllVideos();
          log(
            `✅ Worker: удалено ${deletedCount} видео для аккаунта ${accountIndex}`
          );

          // Собираем статистику после удаления видео
          try {
            log(
              `📊 Worker: собираем статистику после удаления видео для аккаунта ${accountIndex}`
            );
            const stats = await uploader.getProfileStats();
            log(
              `✅ Worker: статистика собрана для аккаунта ${accountIndex}: Подписчиков: ${stats.followers}, Подписок: ${stats.following}, Лайков: ${stats.likes}, Просмотров: ${stats.views}`
            );

            // Сохраняем статистику в базу данных
            const { AccountService } = await import(
              "../services/account.service"
            );
            const accountService = new AccountService();

            // Находим ID аккаунта по cookies
            const video = await prisma.videoUpload.findUnique({
              where: { id: videoId },
              include: { account: true },
            });

            if (video && video.account) {
              await accountService.addAccountStats(
                video.account.id,
                stats,
                "initial"
              );
              log(
                `✅ Worker: статистика сохранена в базу данных для аккаунта ${accountIndex}`
              );
            }
          } catch (statsError: any) {
            log(
              `⚠️ Worker: ошибка при сборе статистики для аккаунта ${accountIndex}: ${statsError.message}`
            );
          }
        } catch (error: any) {
          log(
            `⚠️ Worker: ошибка при удалении видео для аккаунта ${accountIndex}: ${error.message}`
          );
          // Продолжаем загрузку даже если удаление не удалось
        }
      }

      videoUrl = await uploader.uploadVideo({
        videoPath: videoPath,
        caption: caption,
        hashtags: hashtags,
      });

      log(`📹 Видео загружено, URL: ${videoUrl}`);
    } finally {
      await uploader.close();
    }

    await prisma.videoUpload.update({
      where: { id: videoId },
      data: {
        status: "success",
        uploadedUrl: videoUrl,
      },
    });

    await prisma.uploadBatch.update({
      where: { id: batchId },
      data: {
        successCount: { increment: 1 },
      },
    });

    log(`✅ Worker: видео ${videoId} успешно загружено: ${videoUrl}`);

    if (fs.existsSync(videoPath)) {
      fs.unlinkSync(videoPath);
      log(`🗑️ Worker: временный файл удален: ${videoPath}`);
    }

    await incrementProcessedVideos();

    await job.progress(100);
  } catch (error: any) {
    log(`❌ Worker: ошибка при загрузке видео ${videoId}: ${error.message}`);

    await prisma.videoUpload.update({
      where: { id: videoId },
      data: {
        status: "failed",
        errorMessage: error.message,
      },
    });

    await prisma.uploadBatch.update({
      where: { id: batchId },
      data: {
        failedCount: { increment: 1 },
      },
    });

    if (fs.existsSync(videoPath)) {
      fs.unlinkSync(videoPath);
      log(`🗑️ Worker: временный файл удален после провала: ${videoPath}`);
    }

    throw error;
  } finally {
    const batch = await prisma.uploadBatch.findUnique({
      where: { id: batchId },
      include: { videos: true },
    });

    if (batch) {
      const totalProcessed = batch.successCount + batch.failedCount;
      if (totalProcessed === batch.totalVideos) {
        await prisma.uploadBatch.update({
          where: { id: batchId },
          data: { status: "completed" },
        });
        log(
          `✅ Worker: батч ${batchId} полностью завершен (${batch.successCount} успешно, ${batch.failedCount} ошибок)`
        );
      }
    }
  }
}

uploadQueue.process(2, async (job) => {
  try {
    await processUploadJob(job);
  } catch (error: any) {
    log(
      `❌ Worker: критическая ошибка при загрузке видео ${job.data.videoId}: ${error.message}`
    );
    throw error;
  }
});

log("🔄 Upload Worker запущен и готов обрабатывать задачи");

process.on("SIGTERM", async () => {
  log("⏹️ Получен SIGTERM, останавливаем worker...");
  await uploadQueue.close();
  process.exit(0);
});

process.on("SIGINT", async () => {
  log("⏹️ Получен SIGINT, останавливаем worker...");
  await uploadQueue.close();
  process.exit(0);
});
