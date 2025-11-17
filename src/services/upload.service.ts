import * as fs from "fs";
import * as path from "path";
import extract from "extract-zip";

export function distributeVideos(
  videoFiles: string[],
  accounts: string[],
  proxies: string[]
): Array<{
  videoPath: string;
  accountIndex: number;
  accountCookie: string;
  proxy?: string;
}> {
  const distribution: Array<{
    videoPath: string;
    accountIndex: number;
    accountCookie: string;
    proxy?: string;
  }> = [];

  // Распределяем видео по кругу между аккаунтами (round-robin)
  // Пример: 100 видео, 5 аккаунтов
  // Видео 1 → Аккаунт 0
  // Видео 2 → Аккаунт 1
  // Видео 3 → Аккаунт 2
  // Видео 4 → Аккаунт 3
  // Видео 5 → Аккаунт 4
  // Видео 6 → Аккаунт 0 (снова по кругу)
  videoFiles.forEach((videoPath, index) => {
    const accountIndex = index % accounts.length;

    distribution.push({
      videoPath,
      accountIndex: accountIndex,
      accountCookie: accounts[accountIndex],
      proxy: proxies[accountIndex],
    });
  });

  return distribution;
}

export async function extractZipToTemp(zipPath: string, tempDir: string): Promise<string[]> {
  // Извлекаем весь ZIP архив в временную директорию
  await extract(zipPath, { dir: path.resolve(tempDir) });

  const videoFiles: string[] = [];
  const videoExtensions = [".mp4", ".mov", ".avi", ".webm"];

  // Рекурсивная функция для обхода всех файлов
  function findVideoFiles(dir: string) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      // Пропускаем системные файлы macOS и скрытые файлы
      if (
        entry.name.startsWith("._") || // Служебные файлы macOS
        entry.name.startsWith(".") || // Скрытые файлы
        fullPath.includes("__MACOSX") // Системная папка macOS
      ) {
        continue;
      }

      if (entry.isDirectory()) {
        // Рекурсивно обходим поддиректории
        findVideoFiles(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (videoExtensions.includes(ext)) {
          videoFiles.push(fullPath);
        }
      }
    }
  }

  findVideoFiles(tempDir);
  return videoFiles;
}

export function parseTextFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, "utf-8");
  return content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}
