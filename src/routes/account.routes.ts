import express from "express";
import { AccountController } from "../controllers/account.controller";

const router = express.Router();
const accountController = new AccountController();

router.get("/accounts", (req, res) => accountController.getAllAccounts(req, res));
router.get("/accounts/stats", (req, res) => accountController.getAccountStats(req, res));
router.get("/accounts/by-hashtag", (req, res) => accountController.findAccountsByHashtag(req, res));

router.get("/hashtags", (req, res) => accountController.getAllHashtags(req, res));
router.post("/hashtags/update-stats", (req, res) => accountController.updateHashtagStats(req, res));
router.get("/hashtags/stats-history", (req, res) => accountController.getHashtagStatsHistory(req, res));
router.get("/hashtags/export-excel", (req, res) => accountController.exportHashtagStatsToExcel(req, res));

export default router;

