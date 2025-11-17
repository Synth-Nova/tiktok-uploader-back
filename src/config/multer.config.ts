import multer, { StorageEngine } from "multer";
import * as path from "path";
import * as fs from "fs";

const UPLOADS_DIR = path.join(__dirname, "../../uploads");

if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const storage: StorageEngine = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOADS_DIR);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  },
});

export const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    if (file.fieldname === "videos") {
      const allowedZipMimes = [
        "application/zip",
        "application/x-zip-compressed",
        "application/x-zip",
        "multipart/x-zip",
      ];
      if (
        allowedZipMimes.includes(file.mimetype) ||
        file.originalname.endsWith(".zip")
      ) {
        cb(null, true);
      } else {
        cb(
          new Error("Неверный тип файла для videos. Разрешен только ZIP архив")
        );
      }
    } else if (file.fieldname === "accounts" || file.fieldname === "proxies") {
      const allowedTextMimes = ["text/plain", "application/octet-stream"];
      if (
        allowedTextMimes.includes(file.mimetype) ||
        file.originalname.endsWith(".txt")
      ) {
        cb(null, true);
      } else {
        cb(new Error("Неверный тип файла. Разрешен только TXT файл"));
      }
    } else if (file.fieldname === "video") {
      const allowedVideoMimes = [
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-ms-wmv",
        "video/webm",
      ];
      if (allowedVideoMimes.includes(file.mimetype)) {
        cb(null, true);
      } else {
        cb(
          new Error(
            "Неверный тип файла. Разрешены только видео файлы (mp4, mov, avi, wmv, webm)"
          )
        );
      }
    } else {
      cb(null, true);
    }
  },
  limits: {
    fileSize: 50 * 1024 * 1024 * 1024, // 50 ГБ
  },
});
