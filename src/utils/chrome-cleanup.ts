import { exec } from "child_process";
import { promisify } from "util";
import { log } from "../utils";
import { uploadQueue } from "../queues/upload.queue";
import Redis from "ioredis";

const execAsync = promisify(exec);
const CLEANUP_COUNTER_KEY = "chrome:cleanup:counter";
const CLEANUP_THRESHOLD = 200;

const redis = new Redis({
  host: process.env.REDIS_HOST || "localhost",
  port: parseInt(process.env.REDIS_PORT || "6379"),
  password: process.env.REDIS_PASSWORD,
  maxRetriesPerRequest: null,
});

/**
 * Убивает все Chrome процессы без завершения Node процесса
 */
async function killChromeProcesses(): Promise<void> {
  const isWindows = process.platform === "win32";

  try {
    log("🔍 Поиск Chrome процессов для очистки...");

    if (isWindows) {
      try {
        let chromeCount = 0;
        let chromedriverCount = 0;

        try {
          const { stdout: chromeOut } = await execAsync(
            'tasklist /FI "IMAGENAME eq chrome.exe"'
          );
          chromeCount = (chromeOut.match(/chrome\.exe/gi) || []).length;
        } catch (e) {}

        try {
          const { stdout: driverOut } = await execAsync(
            'tasklist /FI "IMAGENAME eq chromedriver.exe"'
          );
          chromedriverCount = (driverOut.match(/chromedriver\.exe/gi) || [])
            .length;
        } catch (e) {}

        const total = chromeCount + chromedriverCount;

        log(`📊 Найдено процессов: Chrome: ${chromeCount}, ChromeDriver: ${chromedriverCount}`);

        if (total === 0) {
          log("✅ Chrome процессы не найдены");
          return;
        }

        log("🗑️ Принудительное завершение всех Chrome процессов...");

        if (chromeCount > 0) {
          try {
            await execAsync("taskkill /F /IM chrome.exe /T");
            log(`✅ Завершено ${chromeCount} процессов chrome.exe`);
          } catch (e: any) {
            log(`⚠️ Ошибка при завершении chrome.exe: ${e.message}`);
          }
        }

        if (chromedriverCount > 0) {
          try {
            await execAsync("taskkill /F /IM chromedriver.exe /T");
            log(`✅ Завершено ${chromedriverCount} процессов chromedriver.exe`);
          } catch (e: any) {
            log(`⚠️ Ошибка при завершении chromedriver.exe: ${e.message}`);
          }
        }

        log(`✅ Chrome процессы (${total}) завершены`);
      } catch (error: any) {
        log(`⚠️ Ошибка при очистке Chrome: ${error.message}`);
      }
    } else {
      try {
        const { stdout: chromePs } = await execAsync(
          "ps aux | grep -i chrome | grep -v grep || true"
        );
        const { stdout: driverPs } = await execAsync(
          "ps aux | grep -i chromedriver | grep -v grep || true"
        );

        const chromeLines = chromePs
          .trim()
          .split("\n")
          .filter((l) => l.length > 0);
        const driverLines = driverPs
          .trim()
          .split("\n")
          .filter((l) => l.length > 0);
        const total = chromeLines.length + driverLines.length;

        log(`📊 Найдено процессов: Chrome: ${chromeLines.length}, ChromeDriver: ${driverLines.length}`);

        if (total === 0) {
          log("✅ Chrome процессы не найдены");
          return;
        }

        log("🗑️ Принудительное завершение всех Chrome процессов...");

        await execAsync("pkill -9 -i chrome || true");
        await execAsync("pkill -9 -i chromedriver || true");

        log(`✅ Chrome процессы (${total}) завершены`);
      } catch (error: any) {
        log(`⚠️ Ошибка при очистке Chrome: ${error.message}`);
      }
    }
  } catch (error: any) {
    log(`❌ Ошибка при завершении Chrome процессов: ${error.message}`);
  }
}

/**
 * Увеличивает счетчик обработанных видео
 */
export async function incrementProcessedVideos(): Promise<void> {
  try {
    const newCount = await redis.incr(CLEANUP_COUNTER_KEY);
    log(`📊 Обработано видео: ${newCount}/${CLEANUP_THRESHOLD}`);

    if (newCount >= CLEANUP_THRESHOLD) {
      log(`🧹 Достигнут лимит ${CLEANUP_THRESHOLD} видео, запускаем очистку Chrome...`);
      await performCleanup();
    }
  } catch (error: any) {
    log(`⚠️ Ошибка при обновлении счетчика: ${error.message}`);
  }
}

/**
 * Выполняет полную очистку: пауза очереди -> убийство Chrome -> возобновление
 */
async function performCleanup(): Promise<void> {
  try {
    log("⏸️ Приостанавливаем очередь загрузки...");
    await uploadQueue.pause();

    log("⏳ Ждем завершения активных задач (10 секунд)...");
    await new Promise((resolve) => setTimeout(resolve, 10000));

    await killChromeProcesses();

    log("⏳ Ждем 5 секунд перед возобновлением...");
    await new Promise((resolve) => setTimeout(resolve, 5000));

    await redis.set(CLEANUP_COUNTER_KEY, "0");
    log("🔄 Счетчик сброшен");

    log("▶️ Возобновляем очередь загрузки...");
    await uploadQueue.resume();

    log("✅ Очистка Chrome завершена, работа продолжается");
  } catch (error: any) {
    log(`❌ Ошибка при выполнении очистки: ${error.message}`);
    try {
      await uploadQueue.resume();
    } catch (e) {
      log(`❌ Не удалось возобновить очередь: ${e}`);
    }
  }
}

/**
 * Получает текущий счетчик обработанных видео
 */
export async function getProcessedVideosCount(): Promise<number> {
  try {
    const count = await redis.get(CLEANUP_COUNTER_KEY);
    return count ? parseInt(count, 10) : 0;
  } catch (error: any) {
    log(`⚠️ Ошибка при получении счетчика: ${error.message}`);
    return 0;
  }
}

/**
 * Сбрасывает счетчик обработанных видео
 */
export async function resetProcessedVideosCount(): Promise<void> {
  try {
    await redis.set(CLEANUP_COUNTER_KEY, "0");
    log("🔄 Счетчик обработанных видео сброшен");
  } catch (error: any) {
    log(`⚠️ Ошибка при сбросе счетчика: ${error.message}`);
  }
}

/**
 * Закрывает соединение с Redis
 */
export async function closeRedisConnection(): Promise<void> {
  await redis.quit();
}

