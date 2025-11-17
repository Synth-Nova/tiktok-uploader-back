import { Router } from "express";
import { StatsController } from "../controllers/stats.controller";

const router = Router();
const statsController = new StatsController();

router.get("/stats", (req, res) => statsController.getStats(req, res));
router.get("/stats/progress", (req, res) => statsController.getStatsProgress(req, res));
router.get("/stats/progress/active", (req, res) => statsController.getActiveStatsProgress(req, res));
router.delete("/stats/progress/clear", (req, res) => statsController.clearOldStatsProgress(req, res));

export default router;

