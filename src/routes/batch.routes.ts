import { Router } from "express";
import { BatchController } from "../controllers/batch.controller";
import { upload } from "../config/multer.config";

const router = Router();
const batchController = new BatchController();

router.post(
  "/batch-upload",
  upload.fields([
    { name: "videos", maxCount: 1 },
    { name: "accounts", maxCount: 1 },
    { name: "proxies", maxCount: 1 },
  ]),
  (req, res) => batchController.batchUpload(req, res)
);

router.get("/batches", (req, res) => batchController.getAllBatches(req, res));

router.get("/batches/:id", (req, res) => batchController.getBatchById(req, res));

export default router;

