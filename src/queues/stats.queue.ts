import Queue from "bull";
import { redisConfig } from "../config/redis.config";

export interface StatsJobData {
  hashtag: string;
  accountId: string;
  accountCookies: string;
  proxy?: string;
  userAgent: string;
}

export const statsQueue = new Queue<StatsJobData>(
  "stats-update",
  redisConfig
);

statsQueue.on("completed", (job) => {
  console.log(`✅ Stats job ${job.id} completed for account ${job.data.accountId}`);
});

statsQueue.on("failed", (job, err) => {
  const attempts = job?.attemptsMade || 0;
  const maxAttempts = job?.opts.attempts || 1;

  if (attempts >= maxAttempts) {
    console.warn(
      `❌ Stats job ${job?.id} окончательно провален после ${attempts} попыток:`,
      err.message
    );
  } else {
    console.log(
      `⚠️ Stats job ${job?.id} failed (попытка ${attempts}/${maxAttempts}), будет retry:`,
      err.message
    );
  }
});

statsQueue.on("progress", (job, progress) => {
  console.log(`📊 Stats job ${job.id} progress: ${progress}%`);
});

statsQueue.on("stalled", (job) => {
  console.warn(
    `⚠️ Stats job ${job.id} stalled (попытка ${job.attemptsMade}/${
      job.opts.attempts || 1
    })`
  );
});

statsQueue.on("waiting", (jobId) => {
  console.log(`⏳ Stats job ${jobId} waiting in queue`);
});

statsQueue.on("active", (job) => {
  const attempt = job.attemptsMade + 1;
  const maxAttempts = job.opts.attempts || 1;

  if (attempt > 1) {
    console.log(`🔄 Stats job ${job.id} started (попытка ${attempt}/${maxAttempts})`);
  } else {
    console.log(`🚀 Stats job ${job.id} started`);
  }
});

