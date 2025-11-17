import * as fs from "fs";
import * as path from "path";
import prisma from "../prisma";
import { uploadQueue, UploadJobData } from "../queues/upload.queue";
import {
  distributeVideos,
  extractZipToTemp,
  parseTextFile,
} from "./upload.service";
import { log, getNext10MinSlot } from "../utils";
import { AccountService } from "./account.service";

const TEMP_DIR = path.join(__dirname, "../../temp");

if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

export interface BatchUploadResult {
  success: boolean;
  message?: string;
  data?: {
    batchId: string;
    totalVideos?: number;
    totalAccounts?: number;
    distribution?: Array<{
      video: string;
      accountIndex: number;
      scheduledAt?: string;
    }>;
    estimatedCompletionTime?: string;
  };
  error?: string;
}

export class BatchService {
  private accountService = new AccountService();

  async createBatchUpload(
    videosZipPath: string,
    accountsFilePath: string,
    proxiesFilePath: string,
    hashtags: string = "",
    description: string = ""
  ): Promise<BatchUploadResult> {
    let extractedVideos: string[] = [];
    let batchId: string | null = null;

    try {
      // Парсим файлы с аккаунтами и прокси
      const accounts = parseTextFile(accountsFilePath);
      const proxies = parseTextFile(proxiesFilePath);

      // Валидация: количество прокси должно совпадать с количеством аккаунтов
      if (accounts.length !== proxies.length) {
        throw new Error(
          `Количество прокси (${proxies.length}) не совпадает с количеством аккаунтов (${accounts.length})`
        );
      }

      if (accounts.length === 0) {
        throw new Error("Файл с аккаунтами пуст");
      }

      // Создаем временную директорию для этого батча
      const batchTempDir = path.join(TEMP_DIR, `batch-${Date.now()}`);
      fs.mkdirSync(batchTempDir, { recursive: true });

      log(`📦 Файлы загружены, начинаем обработку в фоне`);

      // Создаем запись о батче в БД со статусом "processing"
      const batch = await prisma.uploadBatch.create({
        data: {
          totalVideos: 0, // Обновим после распаковки
          totalAccounts: accounts.length,
          status: "processing",
          hashtags: hashtags || null,
          description: description || null,
        },
      });

      batchId = batch.id;

      log(`✅ Батч ${batch.id} создан, возвращаем ответ клиенту`);

      // СРАЗУ возвращаем ответ клиенту
      const response = {
        success: true,
        message: "Файлы успешно загружены, обработка началась в фоне",
        data: {
          batchId: batch.id,
        },
      };

      // Запускаем обработку в фоне (распаковка + создание задач)
      this.processUploadInBackground(
        batch.id,
        videosZipPath,
        accountsFilePath,
        proxiesFilePath,
        batchTempDir,
        accounts,
        proxies,
        hashtags,
        description
      );

      return response;
    } catch (error: any) {
      // Удаляем извлеченные видео асинхронно
      if (extractedVideos.length > 0) {
        this.cleanupFilesAsync(extractedVideos);
      }

      // Обновляем статус батча на failed, если он был создан
      if (batchId) {
        await prisma.uploadBatch.update({
          where: { id: batchId },
          data: { status: "failed" },
        });
      }

      throw error;
    }
  }

  async getAllBatches() {
    return await prisma.uploadBatch.findMany({
      orderBy: { createdAt: "desc" },
      take: 50,
    });
  }

  async getBatchById(id: string) {
    return await prisma.uploadBatch.findUnique({
      where: { id },
      include: {
        videos: {
          orderBy: { createdAt: "asc" },
        },
      },
    });
  }

  async getStats() {
    const totalBatches = await prisma.uploadBatch.count();
    const totalVideos = await prisma.videoUpload.count();
    const successVideos = await prisma.videoUpload.count({
      where: { status: "success" },
    });
    const failedVideos = await prisma.videoUpload.count({
      where: { status: "failed" },
    });
    const processingVideos = await prisma.videoUpload.count({
      where: { status: { in: ["pending", "uploading"] } },
    });

    return {
      totalBatches,
      totalVideos,
      successVideos,
      failedVideos,
      processingVideos,
      successRate:
        totalVideos > 0 ? Math.round((successVideos / totalVideos) * 100) : 0,
    };
  }

  private cleanupFiles(filePaths: string[]) {
    filePaths.forEach((filePath) => {
      if (filePath && fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    });
  }

  // Обработка загрузки в фоновом режиме (распаковка + создание задач)
  private async processUploadInBackground(
    batchId: string,
    videosZipPath: string,
    accountsFilePath: string,
    proxiesFilePath: string,
    batchTempDir: string,
    accounts: string[],
    proxies: string[],
    hashtags: string,
    description: string
  ) {
    setImmediate(async () => {
      try {
        log(`🔄 Начинаем распаковку ZIP для батча ${batchId}`);

        // Распаковываем видео из ZIP
        const extractedVideos = await extractZipToTemp(
          videosZipPath,
          batchTempDir
        );

        log(
          `✅ Распаковано ${extractedVideos.length} видео для батча ${batchId}`
        );

        if (extractedVideos.length === 0) {
          throw new Error(
            "ZIP архив не содержит видео файлов (.mp4, .mov, .avi, .webm)"
          );
        }

        // Обновляем количество видео в батче
        await prisma.uploadBatch.update({
          where: { id: batchId },
          data: { totalVideos: extractedVideos.length },
        });

        // Распределяем видео между аккаунтами
        const distribution = distributeVideos(
          extractedVideos,
          accounts,
          proxies
        );

        log(`📹 Распределение видео для батча ${batchId} завершено`);

        // Создаем задачи
        await this.createJobsInBackground(
          batchId,
          distribution,
          accounts,
          extractedVideos.length,
          hashtags,
          description,
          proxies
        );

        // Удаляем загруженные файлы
        this.cleanupFilesAsync([
          videosZipPath,
          accountsFilePath,
          proxiesFilePath,
        ]);

        log(`✅ Обработка батча ${batchId} полностью завершена`);
      } catch (error: any) {
        log(`❌ Ошибка при обработке батча ${batchId}: ${error.message}`);

        // Обновляем статус батча на failed
        await prisma.uploadBatch.update({
          where: { id: batchId },
          data: { status: "failed" },
        });

        // Удаляем загруженные файлы
        this.cleanupFilesAsync([
          videosZipPath,
          accountsFilePath,
          proxiesFilePath,
        ]);
      }
    });
  }

  // Создание задач в фоновом режиме
  private async createJobsInBackground(
    batchId: string,
    distribution: Array<{
      videoPath: string;
      accountIndex: number;
      accountCookie: string;
      proxy?: string;
    }>,
    accounts: string[],
    totalVideos: number,
    hashtags: string,
    description: string,
    proxies: string[]
  ) {
    try {
      log(
        `🔄 Начинаем создание ${distribution.length} задач для батча ${batchId}`
      );

      const accountsData = await Promise.all(
        accounts.map(async (accountCookie, index) => {
          const accountData = await this.accountService.findOrCreateAccount(
            accountCookie,
            undefined,
            proxies[index]
          );

          // Логируем информацию о новых аккаунтах
          if (accountData.isNew) {
            log(`🆕 Новый аккаунт обнаружен (индекс ${index}), видео будут удалены перед загрузкой`);
          }

          return accountData;
        })
      );

      log(`📊 Обработано аккаунтов: ${accountsData.length}`);

      if (hashtags && hashtags.trim()) {
        const hashtagArray = hashtags
          .split(",")
          .map((tag) => tag.trim())
          .filter((tag) => tag);
        log(
          `🏷️ Добавляем хэштеги [${hashtagArray.join(", ")}] ко всем ${accountsData.length} аккаунтам`
        );

        // СНАЧАЛА создаем все хэштеги заранее (решение race condition)
        log(`🔧 Предварительное создание хэштегов...`);
        await this.accountService.ensureHashtagsExist(hashtagArray);
        log(`✅ Все хэштеги подготовлены`);

        // Теперь безопасно добавляем связи параллельно
        const hashtagResults = await Promise.allSettled(
          accountsData.map(async (accountData, index) => {
            try {
              log(`🏷️ [${index + 1}/${accountsData.length}] Добавляем хэштеги к аккаунту ${accountData.id.substring(0, 8)}...`);
              await this.accountService.addHashtagsToAccount(
                accountData.id,
                hashtagArray
              );
              log(`✅ [${index + 1}/${accountsData.length}] Хэштеги добавлены к аккаунту ${accountData.id.substring(0, 8)}...`);
              return { success: true, accountId: accountData.id };
            } catch (error: any) {
              log(`❌ [${index + 1}/${accountsData.length}] Ошибка добавления хэштегов к аккаунту ${accountData.id.substring(0, 8)}...: ${error.message}`);
              return { success: false, accountId: accountData.id, error: error.message };
            }
          })
        );

        // Подсчитываем результаты
        const successful = hashtagResults.filter(r => r.status === 'fulfilled' && r.value.success).length;
        const failed = hashtagResults.length - successful;
        
        log(`✅ Хэштеги добавлены: ${successful}/${accountsData.length} аккаунтов успешно, ${failed} с ошибками`);
        
        if (failed > 0) {
          log(`⚠️ Детали ошибок при добавлении хэштегов:`);
          hashtagResults.forEach((result, index) => {
            if (result.status === 'rejected' || (result.status === 'fulfilled' && !result.value.success)) {
              const error = result.status === 'rejected' ? result.reason : result.value.error;
              log(`  - Аккаунт ${index}: ${error}`);
            }
          });
        }
      } else {
        log(`ℹ️ Хэштеги не указаны для батча ${batchId}`);
      }

      const accountSeen = new Map<number, boolean>();
      const accountLastTime = new Map<number, Date>();
      const now = new Date();

      const scheduledTimes = distribution.map((item, index) => {
        let scheduledAt: Date;

        if (!accountSeen.has(item.accountIndex)) {
          scheduledAt = now;
          accountSeen.set(item.accountIndex, true);
        } else {
          const lastTimeForAccount =
            accountLastTime.get(item.accountIndex) || now;
          scheduledAt = getNext10MinSlot(lastTimeForAccount);
        }

        accountLastTime.set(item.accountIndex, scheduledAt);
        return scheduledAt;
      });

      const batchSize = 50;
      for (let i = 0; i < distribution.length; i += batchSize) {
        const chunk = distribution.slice(i, i + batchSize);

        await Promise.all(
          chunk.map(async (item, chunkIndex) => {
            const index = i + chunkIndex;
            const accountData = accountsData[item.accountIndex];
            const scheduledAt = scheduledTimes[index];

            const videoUpload = await prisma.videoUpload.create({
              data: {
                batchId: batchId,
                accountId: accountData.id,
                videoFileName: path.basename(item.videoPath),
                accountIndex: item.accountIndex,
                accountCookie: item.accountCookie,
                proxy: item.proxy,
                caption: description || `Video ${index + 1}`,
                hashtags: hashtags || "tiktok,viral",
                status: "pending",
              },
            });

            const delay = scheduledAt.getTime() - Date.now();

            const jobData: UploadJobData = {
              batchId: batchId,
              videoId: videoUpload.id,
              videoPath: item.videoPath,
              accountCookie: item.accountCookie,
              accountIndex: item.accountIndex,
              proxy: item.proxy,
              caption: videoUpload.caption || `Video ${index + 1}`,
              hashtags: videoUpload.hashtags
                ? videoUpload.hashtags.split(",")
                : [],
              scheduledAt: scheduledAt,
              userAgent: accountData.userAgent,
              deleteExistingVideos: accountData.isNew, // Удаляем видео только для новых аккаунтов
            };

            await uploadQueue.add(jobData, {
              jobId: videoUpload.id,
              delay: delay > 0 ? delay : 0,
              priority: index + 1,
              attempts: 1,
            });
          })
        );

        log(
          `📋 Создано ${Math.min(i + batchSize, distribution.length)}/${
            distribution.length
          } задач`
        );
      }

      log(`✅ Все ${distribution.length} задач для батча ${batchId} созданы`);
    } catch (error: any) {
      log(
        `❌ Ошибка при создании задач в фоне для батча ${batchId}: ${error.message}`
      );

      // Обновляем статус батча на failed
      await prisma.uploadBatch.update({
        where: { id: batchId },
        data: { status: "failed" },
      });
    }
  }

  // Асинхронная очистка файлов без ожидания завершения
  private cleanupFilesAsync(filePaths: string[]) {
    log("Запускаем удаление файлов");
    // Запускаем удаление в фоне, не блокируя основной поток
    setImmediate(() => {
      filePaths.forEach((filePath) => {
        if (filePath && fs.existsSync(filePath)) {
          try {
            fs.unlinkSync(filePath);
            log(`🗑️ Удален файл: ${filePath}`);
          } catch (error: any) {
            log(`⚠️ Не удалось удалить файл ${filePath}: ${error.message}`);
          }
        }
      });
    });
  }
}
