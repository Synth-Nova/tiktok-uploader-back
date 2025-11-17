import { Router } from "express";
import batchRoutes from "./batch.routes";
import videoRoutes from "./video.routes";
import statsRoutes from "./stats.routes";
import downloadRoutes from "./download.routes";
import accountRoutes from "./account.routes";

const router = Router();

router.use("/api", batchRoutes);
router.use("/api", videoRoutes);
router.use("/api", statsRoutes);
router.use("/api", downloadRoutes);
router.use("/api", accountRoutes);

export default router;

