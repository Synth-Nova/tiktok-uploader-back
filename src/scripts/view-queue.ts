import { uploadQueue } from "../queues/upload.queue";
import { log } from "../utils";

async function viewQueue() {
  try {
    log("📊 Просмотр состояния очереди...\n");

    // Получаем все типы задач
    const waiting = await uploadQueue.getWaiting();
    const active = await uploadQueue.getActive();
    const delayed = await uploadQueue.getDelayed();
    const completed = await uploadQueue.getCompleted();
    const failed = await uploadQueue.getFailed();

    const total = waiting.length + active.length + delayed.length;

    // Статистика
    log("=" .repeat(80));
    log("📈 ОБЩАЯ СТАТИСТИКА");
    log("=" .repeat(80));
    log(`Всего активных задач: ${total}`);
    log(`  ⏳ Ожидают выполнения: ${waiting.length}`);
    log(`  🔄 Выполняются: ${active.length}`);
    log(`  ⏰ Отложены (запланированы): ${delayed.length}`);
    log(`  ✅ Завершены: ${completed.length}`);
    log(`  ❌ Ошибок: ${failed.length}`);
    log("=" .repeat(80));
    log("");

    // Отображаем активные задачи
    if (active.length > 0) {
      log("🔄 ВЫПОЛНЯЮТСЯ СЕЙЧАС:");
      log("-" .repeat(80));
      for (const job of active) {
        const progress = await job.progress();
        log(`ID: ${job.id}`);
        log(`  Батч: ${job.data.batchId}`);
        log(`  Видео: ${job.data.videoPath.split('/').pop()}`);
        log(`  Аккаунт: ${job.data.accountIndex}`);
        log(`  Прогресс: ${progress}%`);
        log(`  Попытка: ${job.attemptsMade + 1}/${job.opts.attempts || 3}`);
        log("-" .repeat(80));
      }
      log("");
    }

    // Отображаем отложенные задачи (запланированные)
    if (delayed.length > 0) {
      log("⏰ ЗАПЛАНИРОВАННЫЕ ЗАДАЧИ:");
      log("-" .repeat(80));
      
      // Сортируем по времени выполнения
      const sortedDelayed = delayed.sort((a, b) => {
        const delayA = a.opts.delay || 0;
        const delayB = b.opts.delay || 0;
        const timestampA = a.timestamp || 0;
        const timestampB = b.timestamp || 0;
        return (timestampA + delayA) - (timestampB + delayB);
      });

      for (const job of sortedDelayed) {
        const delay = job.opts.delay || 0;
        const timestamp = job.timestamp || 0;
        const scheduledTime = new Date(timestamp + delay);
        const now = new Date();
        const minutesUntil = Math.round((scheduledTime.getTime() - now.getTime()) / 1000 / 60);
        
        log(`ID: ${job.id}`);
        log(`  Батч: ${job.data.batchId}`);
        log(`  Видео: ${job.data.videoPath.split('/').pop()}`);
        log(`  Аккаунт: ${job.data.accountIndex}`);
        log(`  Запланировано на: ${scheduledTime.toLocaleString('ru-RU')}`);
        log(`  Через: ${minutesUntil > 0 ? minutesUntil + ' минут' : 'сейчас'}`);
        log(`  Приоритет: ${job.opts.priority || 'не задан'}`);
        log("-" .repeat(80));
      }
      log("");
    }

    // Отображаем ожидающие задачи
    if (waiting.length > 0) {
      log("⏳ ОЖИДАЮТ ВЫПОЛНЕНИЯ:");
      log("-" .repeat(80));
      const displayCount = Math.min(waiting.length, 10);
      for (let i = 0; i < displayCount; i++) {
        const job = waiting[i];
        log(`ID: ${job.id}`);
        log(`  Батч: ${job.data.batchId}`);
        log(`  Видео: ${job.data.videoPath.split('/').pop()}`);
        log(`  Аккаунт: ${job.data.accountIndex}`);
        log("-" .repeat(80));
      }
      if (waiting.length > 10) {
        log(`... и еще ${waiting.length - 10} задач`);
      }
      log("");
    }

    // Отображаем последние завершенные
    if (completed.length > 0) {
      log("✅ ПОСЛЕДНИЕ ЗАВЕРШЕННЫЕ (последние 5):");
      log("-" .repeat(80));
      const displayCount = Math.min(completed.length, 5);
      for (let i = 0; i < displayCount; i++) {
        const job = completed[i];
        if (!job.data || !job.data.videoPath) {
          continue; // Пропускаем задачи без данных
        }
        const finishedTime = job.finishedOn ? new Date(job.finishedOn).toLocaleString('ru-RU') : 'неизвестно';
        log(`ID: ${job.id}`);
        log(`  Батч: ${job.data.batchId}`);
        log(`  Видео: ${job.data.videoPath.split('/').pop()}`);
        log(`  Завершено: ${finishedTime}`);
        log("-" .repeat(80));
      }
      log("");
    }

    // Отображаем последние ошибки
    if (failed.length > 0) {
      log("❌ ПОСЛЕДНИЕ ОШИБКИ (последние 5):");
      log("-" .repeat(80));
      const displayCount = Math.min(failed.length, 5);
      for (let i = 0; i < displayCount; i++) {
        const job = failed[i];
        if (!job.data || !job.data.videoPath) {
          continue; // Пропускаем задачи без данных
        }
        const failedTime = job.failedReason ? new Date(job.processedOn || Date.now()).toLocaleString('ru-RU') : 'неизвестно';
        log(`ID: ${job.id}`);
        log(`  Батч: ${job.data.batchId}`);
        log(`  Видео: ${job.data.videoPath.split('/').pop()}`);
        log(`  Ошибка: ${job.failedReason || 'неизвестна'}`);
        log(`  Время: ${failedTime}`);
        log("-" .repeat(80));
      }
      log("");
    }

    // Итоговая информация
    log("=" .repeat(80));
    log("💡 ИНФОРМАЦИЯ:");
    log("  - Задачи сохраняются в Redis и продолжат выполняться после перезапуска");
    log("  - Worker обрабатывает по 2 задачи одновременно");
    log("  - Каждая задача повторяется до 3 раз при ошибке");
    log("=" .repeat(80));

    // Закрываем соединение
    await uploadQueue.close();
    process.exit(0);
  } catch (error: any) {
    log(`❌ Ошибка при просмотре очереди: ${error.message}`);
    await uploadQueue.close();
    process.exit(1);
  }
}

viewQueue();

