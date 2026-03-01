import { Router } from "express";
import { moduleRegistry } from "../state/moduleRegistry.js";

export const modulesRouter = Router();

modulesRouter.get("/", (_req, res) => {
  res.json({ modules: moduleRegistry.list() });
});

modulesRouter.post("/", (req, res) => {
  const { moduleId, alias, zone, backhaulSsid, firmwareVersion } = req.body || {};

  if (!moduleId || typeof moduleId !== "string") {
    return res.status(400).json({ error: "moduleId is required" });
  }

  const moduleRecord = moduleRegistry.upsert({
    moduleId,
    alias,
    zone,
    backhaulSsid,
    firmwareVersion,
    status: "provisioned"
  });

  return res.status(201).json({ module: moduleRecord });
});

modulesRouter.post("/:moduleId/heartbeat", (req, res) => {
  const updated = moduleRegistry.heartbeat(req.params.moduleId, req.body);
  if (!updated) {
    return res.status(404).json({ error: "module not found" });
  }

  return res.json({ module: updated });
});
