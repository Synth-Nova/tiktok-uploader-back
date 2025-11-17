import { Job } from "bull";
import { statsQueue, StatsJobData } from "../queues/stats.queue";
import { log, parseCookies } from "../utils";
import { TikTokUploader } from "../tiktok-uploader";
import { AccountService } from "../services/account.service";
import prisma from "../prisma";

const HEADLESS = process.env.HEADLESS !== "false";
const accountService = new AccountService();

async function processStatsJob(job: Job<StatsJobData>): Promise<void> {
  const { hashtag, accountId, accountCookies, proxy, userAgent } = job.data;

  log(
    `🚀 Stats Worker: начинаем сбор статистики для аккаунта ${accountId} (хэштег: #${hashtag})`
  );

  // Создаем запись о прогрессе
  let progressRecord = await prisma.statsProgress.create({
    data: {
      hashtag,
      accountId,
      status: "processing",
      progress: 0,
      currentStep: "Инициализация",
    },
  });

  try {
    let parsedCookies;
    try {
      const parsed = JSON.parse(accountCookies);
      if (Array.isArray(parsed)) {
        parsedCookies = parseCookies(accountCookies);
      } else {
        parsedCookies = parsed;
      }
    } catch (e) {
      parsedCookies = parseCookies(accountCookies);
    }

    // Обновляем прогресс: инициализация
    await prisma.statsProgress.update({
      where: { id: progressRecord.id },
      data: {
        progress: 10,
        currentStep: "Инициализация браузера",
      },
    });

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

    try {
      await uploader.initialize();
      
      // Обновляем прогресс: авторизация
      await prisma.statsProgress.update({
        where: { id: progressRecord.id },
        data: {
          progress: 30,
          currentStep: "Авторизация",
        },
      });

      await uploader.login();

      // Обновляем прогресс: сбор статистики профиля
      await prisma.statsProgress.update({
        where: { id: progressRecord.id },
        data: {
          progress: 50,
          currentStep: "Сбор статистики профиля",
        },
      });

      log(`📊 Stats Worker: собираем статистику для аккаунта ${accountId}`);
      const stats = await uploader.getProfileStats();

      const username = stats.username;

      // Сохраняем промежуточные результаты
      await prisma.statsProgress.update({
        where: { id: progressRecord.id },
        data: {
          progress: 60,
          followers: stats.followers,
          following: stats.following,
          likes: stats.likes,
          username: username,
        },
      });

      // Собираем просмотры со всех видео (только при ручном обновлении)
      if (username) {
        log(
          `📹 Stats Worker: собираем просмотры со всех видео для аккаунта ${accountId}`
        );
        
        // Обновляем прогресс: сбор просмотров
        await prisma.statsProgress.update({
          where: { id: progressRecord.id },
          data: {
            progress: 70,
            currentStep: "Сбор просмотров видео",
          },
        });

        try {
          const totalViews = await uploader.collectVideoViews(username);
          stats.views = totalViews;
          log(`✅ Stats Worker: собрано ${totalViews} просмотров`);
          
          // Обновляем просмотры в прогрессе
          await prisma.statsProgress.update({
            where: { id: progressRecord.id },
            data: {
              views: totalViews,
            },
          });
        } catch (error: any) {
          log(`⚠️ Stats Worker: ошибка при сборе просмотров: ${error.message}`);
          // Продолжаем без просмотров
        }

        // Обновляем username в базе данных
        try {
          await prisma.account.update({
            where: { id: accountId },
            data: { username: username },
          });
          log(`✅ Stats Worker: username (@${username}) обновлен в базе`);
        } catch (error: any) {
          log(
            `⚠️ Stats Worker: ошибка при обновлении username: ${error.message}`
          );
        }
      }

      // Обновляем прогресс: сохранение данных
      await prisma.statsProgress.update({
        where: { id: progressRecord.id },
        data: {
          progress: 90,
          currentStep: "Сохранение данных",
        },
      });

      // Сохраняем статистику в базу данных
      await accountService.addAccountStats(accountId, stats, "manual");

      log(
        `✅ Stats Worker: статистика обновлена для аккаунта ${accountId}: Подписчиков: ${stats.followers}, Подписок: ${stats.following}, Лайков: ${stats.likes}, Просмотров: ${stats.views}`
      );

      // Завершаем с успехом
      await prisma.statsProgress.update({
        where: { id: progressRecord.id },
        data: {
          status: "completed",
          progress: 100,
          currentStep: "Завершено",
          completedAt: new Date(),
        },
      });

      await job.progress(100);
    } finally {
      await uploader.close();
    }
  } catch (error: any) {
    log(
      `❌ Stats Worker: ошибка при сборе статистики для аккаунта ${accountId}: ${error.message}`
    );
    
    // Обновляем прогресс с ошибкой
    await prisma.statsProgress.update({
      where: { id: progressRecord.id },
      data: {
        status: "failed",
        errorMessage: error.message,
        completedAt: new Date(),
      },
    });
    
    throw error;
  }
}

statsQueue.process(2, async (job) => {
  try {
    await processStatsJob(job);
  } catch (error: any) {
    log(
      `❌ Stats Worker: критическая ошибка при обработке задачи ${job.id}: ${error.message}`
    );
    throw error;
  }
});

log("🔄 Stats Worker запущен и готов обрабатывать задачи");

process.on("SIGTERM", async () => {
  log("⏹️ Получен SIGTERM, останавливаем stats worker...");
  await statsQueue.close();
  process.exit(0);
});

process.on("SIGINT", async () => {
  log("⏹️ Получен SIGINT, останавливаем stats worker...");
  await statsQueue.close();
  process.exit(0);
});
