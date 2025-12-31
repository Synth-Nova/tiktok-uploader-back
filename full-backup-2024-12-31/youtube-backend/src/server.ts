import express from "express";
import cors from "cors";
import youtubeRoutes from "./routes/youtube.routes";
import { log } from "./utils";

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use("/api", youtubeRoutes);

// Root route
app.get("/", (req, res) => {
  res.json({
    service: "YouTube Uploader API",
    version: "1.0.0",
    endpoints: {
      "POST /api/batch-upload": "Upload videos batch",
      "GET /api/batch/all": "Get all batches",
      "GET /api/batch/:id": "Get batch by ID",
      "GET /api/health": "Health check",
    },
  });
});

// Error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  log(`❌ Error: ${err.message}`);
  res.status(500).json({ success: false, error: err.message });
});

// Start server
app.listen(PORT, () => {
  log(`🚀 YouTube Uploader API запущен на порту ${PORT}`);
  log(`📍 http://localhost:${PORT}`);
});

export default app;
