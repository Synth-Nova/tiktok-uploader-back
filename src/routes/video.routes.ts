import { Router } from "express";
import { VideoController } from "../controllers/video.controller";
import { upload } from "../config/multer.config";

const router = Router();
const videoController = new VideoController();

router.post("/upload", upload.single("video"), (req, res) =>
  videoController.uploadSingle(req, res)
);

export default router;

