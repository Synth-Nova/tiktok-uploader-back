import Redis from "ioredis";
import { log } from "../utils";

async function flushRedis() {
  const redis = new Redis({
    host: process.env.REDIS_HOST || "localhost",
    port: parseInt(process.env.REDIS_PORT || "6379"),
    password: process.env.REDIS_PASSWORD,
  });

  try {
    log("🗑️ Очистка Redis...");
    
    // Получаем количество ключей до очистки
    const keysBefore = await redis.dbsize();
    log(`📊 Ключей в Redis до очистки: ${keysBefore}`);

    // Очищаем все базы данных
    await redis.flushall();
    
    // Проверяем результат
    const keysAfter = await redis.dbsize();
    log(`✅ Redis полностью очищен!`);
    log(`📊 Ключей в Redis после очистки: ${keysAfter}`);

    await redis.quit();
    process.exit(0);
  } catch (error: any) {
    log(`❌ Ошибка при очистке Redis: ${error.message}`);
    await redis.quit();
    process.exit(1);
  }
}

flushRedis();

