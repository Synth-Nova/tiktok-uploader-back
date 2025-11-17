import Queue from "bull";
import { redisConfig } from "../config/redis.config";

export interface UploadJobData {
  batchId: string;
  videoId: string;
  videoPath: string;
  accountCookie: string;
  accountIndex: number;
  proxy?: string;
  caption: string;
  hashtags: string[];
  scheduledAt: Date;
  userAgent: string;
  deleteExistingVideos?: boolean; // Флаг для удаления существующих видео (для новых аккаунтов)
}

export const uploadQueue = new Queue<UploadJobData>(
  "video-upload",
  redisConfig
);

uploadQueue.on("completed", (job) => {
  console.log(`✅ Job ${job.id} completed for batch ${job.data.batchId}`);
});

uploadQueue.on("failed", (job, err) => {
  const attempts = job?.attemptsMade || 0;
  const maxAttempts = job?.opts.attempts || 1;

  if (attempts >= maxAttempts) {
    console.warn(
      `❌ Job ${job?.id} окончательно провален после ${attempts} попыток:`,
      err.message
    );
  } else {
    console.log(
      `⚠️ Job ${job?.id} failed (попытка ${attempts}/${maxAttempts}), будет retry:`,
      err.message
    );
  }
});

uploadQueue.on("progress", (job, progress) => {
  console.log(`📊 Job ${job.id} progress: ${progress}%`);
});

uploadQueue.on("stalled", (job) => {
  console.warn(
    `⚠️ Job ${job.id} stalled (попытка ${job.attemptsMade}/${
      job.opts.attempts || 1
    })`
  );
});

uploadQueue.on("waiting", (jobId) => {
  console.log(`⏳ Job ${jobId} waiting in queue`);
});

uploadQueue.on("active", (job) => {
  const attempt = job.attemptsMade + 1;
  const maxAttempts = job.opts.attempts || 1;

  if (attempt > 1) {
    console.log(`🔄 Job ${job.id} started (попытка ${attempt}/${maxAttempts})`);
  } else {
    console.log(`🚀 Job ${job.id} started`);
  }
});
