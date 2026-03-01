import cors from "cors";
import express from "express";
import morgan from "morgan";
import { config } from "./config.js";
import { modulesRouter } from "./routes/modules.js";

const app = express();

app.use(cors({ origin: config.dashboardOrigin }));
app.use(express.json());
app.use(morgan("dev"));
app.use(express.static("public"));

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "center-module", time: new Date().toISOString() });
});

app.use("/api/modules", modulesRouter);

app.post("/api/provision/token", (req, res) => {
  const moduleId = req.body?.moduleId;
  if (!moduleId || typeof moduleId !== "string") {
    return res.status(400).json({ error: "moduleId is required" });
  }

  const token = Buffer.from(`${moduleId}:${Date.now()}`).toString("base64url");
  return res.status(201).json({ token, expiresInSec: 300 });
});

app.listen(config.port, config.host, () => {
  console.log(`center-module listening on http://${config.host}:${config.port}`);
});
