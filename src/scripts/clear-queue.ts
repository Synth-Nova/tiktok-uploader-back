import { uploadQueue } from "../queues/upload.queue";
import { log } from "../utils";

async function clearQueue() {
  try {
    log("🧹 Начинаем очистку очереди...");

    // Останавливаем все активные задачи (помечаем как failed)
    const activeJobs = await uploadQueue.getActive();
    log(`📊 Найдено активных задач: ${activeJobs.length}`);

    for (const job of activeJobs) {
      try {
        await job.moveToFailed({ message: "Очистка очереди" }, true);
        log(`⏹️  Остановлена активная задача: ${job.id}`);
      } catch (e) {
        log(`⚠️  Не удалось остановить задачу ${job.id}, пропускаем`);
      }
    }

    // Очищаем ожидающие задачи
    const waitingJobs = await uploadQueue.getWaiting();
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
    const delayedJobs = await uploadQueue.getDelayed();
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
    await uploadQueue.empty();
    await uploadQueue.clean(0, "completed");
    await uploadQueue.clean(0, "failed");
    await uploadQueue.clean(0, "active");

    log("✅ Очередь полностью очищена!");

    // Пауза для завершения всех операций
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Закрываем соединение
    await uploadQueue.close();

    log("✅ Соединение с очередью закрыто");
    process.exit(0);
  } catch (error: any) {
    log(`❌ Ошибка при очистке очереди: ${error.message}`);
    await uploadQueue.close();
    process.exit(1);
  }
}

clearQueue();
