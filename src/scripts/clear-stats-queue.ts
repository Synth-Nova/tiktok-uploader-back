import { statsQueue } from "../queues/stats.queue";
import { log } from "../utils";

async function clearStatsQueue() {
  try {
    log("🧹 Начинаем очистку очереди статистики...");

    // Останавливаем все активные задачи (помечаем как failed)
    const activeJobs = await statsQueue.getActive();
    log(`📊 Найдено активных задач: ${activeJobs.length}`);

    for (const job of activeJobs) {
      try {
        await job.moveToFailed({ message: "Очистка очереди статистики" }, true);
        log(`⏹️  Остановлена активная задача: ${job.id}`);
      } catch (e) {
        log(`⚠️  Не удалось остановить задачу ${job.id}, пропускаем`);
      }
    }

    // Очищаем ожидающие задачи
    const waitingJobs = await statsQueue.getWaiting();
    log(`📊 Найдено ожидающих задач: ${waitingJobs.length}`);

    for (const job of waitingJobs) {
      try {
        await job.remove();
        log(`🗑️  Удалена ожидающая задача: ${job.id}`);
      } catch (e) {
        log(`⚠️  Не удалось удалить задачу ${job.id}`);
      }
    }

    // Очищаем отложенные задачи
    const delayedJobs = await statsQueue.getDelayed();
    log(`📊 Найдено отложенных задач: ${delayedJobs.length}`);

    for (const job of delayedJobs) {
      try {
        await job.remove();
        log(`🗑️  Удалена отложенная задача: ${job.id}`);
      } catch (e) {
        log(`⚠️  Не удалось удалить задачу ${job.id}`);
      }
    }

    // Очищаем все задачи разом
    await statsQueue.empty();
    await statsQueue.clean(0, "completed");
    await statsQueue.clean(0, "failed");
    await statsQueue.clean(0, "active");

    log("✅ Очередь статистики полностью очищена!");

    // Пауза для завершения всех операций
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Закрываем соединение
    await statsQueue.close();

    log("✅ Соединение с очередью закрыто");
    process.exit(0);
  } catch (error: any) {
    log(`❌ Ошибка при очистке очереди статистики: ${error.message}`);
    await statsQueue.close();
    process.exit(1);
  }
}

clearStatsQueue();

