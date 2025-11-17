import dotenv from "dotenv";
dotenv.config({
  path: process.env.NODE_ENV === "production" ? ".env.production" : ".env",
});

import express, { Application } from "express";
import cors from "cors";
import routes from "./routes";
import { log } from "./utils";

const app: Application = express();
const PORT = process.env.PORT || 3000;
const HEADLESS = process.env.HEADLESS !== "false";

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(routes);

const server = app.listen(PORT, () => {
  log(`🚀 TikTok Uploader API запущен на порту ${PORT}`);
  log(`🖥️  Режим: ${HEADLESS ? "headless (без окна)" : "с окном браузера"}`);
  log(`📖 http://localhost:${PORT}`);
});

// Увеличиваем таймауты для больших файлов (30 минут)
server.setTimeout(30 * 60 * 1000); // 30 минут
server.headersTimeout = 30 * 60 * 1000; // 30 минут
server.requestTimeout = 30 * 60 * 1000; // 30 минут

export default app;
