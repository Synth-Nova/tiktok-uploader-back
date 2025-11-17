import { Router } from "express";
import { DownloadController } from "../controllers/download.controller";

const router = Router();
const downloadController = new DownloadController();

router.get("/download/batch/:id/links", (req, res) =>
  downloadController.downloadBatchLinks(req, res)
);

export default router;

