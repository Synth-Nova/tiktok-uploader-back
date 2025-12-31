import { Router } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { batchUpload, getBatches, getBatchById } from "../controllers/youtube.controller";

const router = Router();

// Создаем директорию для загрузок
const uploadDir = path.join(__dirname, "../../uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Настройка multer для загрузки файлов
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + "-" + file.originalname);
  },
});

const upload = multer({
  storage,
  limits: {
    fileSize: 500 * 1024 * 1024, // 500 MB
  },
});

// Routes
router.post(
  "/batch-upload",
  upload.fields([
    { name: "videos", maxCount: 1 },
    { name: "accounts", maxCount: 1 },
    { name: "proxies", maxCount: 1 },
  ]),
  batchUpload
);

router.get("/batch/all", getBatches);
router.get("/batch/:id", getBatchById);

// Health check
router.get("/health", (req, res) => {
  res.json({ status: "ok", service: "youtube-uploader" });
});

export default router;
