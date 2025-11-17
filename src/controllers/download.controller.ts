import { Request, Response } from "express";
import prisma from "../prisma";

export class DownloadController {
  async downloadBatchLinks(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const batch = await prisma.uploadBatch.findUnique({
        where: { id },
        include: {
          videos: {
            where: {
              status: "success",
              uploadedUrl: { not: null },
            },
            orderBy: { createdAt: "asc" },
          },
        },
      });

      if (!batch) {
        res.status(404).json({
          success: false,
          error: "Батч не найден",
        });
        return;
      }

      // Собираем ссылки
      const links = batch.videos
        .map((video: any) => video.uploadedUrl)
        .filter((url: any): url is string => url !== null)
        .join("\n");

      if (!links) {
        res.status(400).json({
          success: false,
          error: "В этом батче нет успешно загруженных видео",
        });
        return;
      }

      // Формируем имя файла
      const fileName = `batch_${id}_links.txt`;

      // Отправляем файл
      res.setHeader("Content-Type", "text/plain; charset=utf-8");
      res.setHeader(
        "Content-Disposition",
        `attachment; filename="${fileName}"`
      );
      res.send(links);
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }
}
