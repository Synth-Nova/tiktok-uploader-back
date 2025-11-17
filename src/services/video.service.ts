import * as fs from "fs";
import * as path from "path";
import { TikTokUploader, VideoConfig } from "../tiktok-uploader";
import { Credentials, log, parseCookies } from "../utils";

export class VideoService {
  async uploadSingleVideo(
    videoPath: string,
    cookies: string,
    caption: string,
    hashtags: string,
    headless: boolean = true
  ): Promise<string> {
    let uploader: TikTokUploader | null = null;

    try {
      const absVideoPath = path.resolve(videoPath);

      if (!fs.existsSync(absVideoPath)) {
        throw new Error(`Видео файл не найден: ${absVideoPath}`);
      }

      let parsedCookies;
      try {
        parsedCookies = JSON.parse(cookies);
      } catch (e) {
        parsedCookies = parseCookies(cookies);
      }

      const hashtagsArray = hashtags
        ? hashtags
            .split(",")
            .map((tag: string) => tag.trim())
            .filter((tag: string) => tag.length > 0)
        : [];

      const credentials: Credentials = {
        username: "",
        password: "",
        email: "",
        email_password: "",
        cookies_string: "",
        cookies: parsedCookies,
      };

      uploader = new TikTokUploader(credentials, headless);

      await uploader.initialize();
      await uploader.login();

      const videoConfig: VideoConfig = {
        videoPath: absVideoPath,
        caption: caption,
        hashtags: hashtagsArray,
      };

      const videoUrl = await uploader.uploadVideo(videoConfig);

      // Удаляем временный файл
      if (fs.existsSync(absVideoPath)) {
        fs.unlinkSync(absVideoPath);
        log(`🗑️  Временный файл удален: ${absVideoPath}`);
      }

      return videoUrl;
    } catch (error) {
      throw error;
    } finally {
      if (uploader) {
        try {
          await uploader.close();
        } catch (e) {
          log(`⚠️ Ошибка при закрытии браузера: ${e}`);
        }
      }
    }
  }
}
