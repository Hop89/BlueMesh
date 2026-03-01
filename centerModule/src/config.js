import dotenv from "dotenv";

dotenv.config();

const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const config = {
  host: process.env.HOST || "0.0.0.0",
  port: toNumber(process.env.PORT, 8080),
  dashboardOrigin: process.env.DASHBOARD_ORIGIN || "*",
  moduleHeartbeatTtlSec: toNumber(process.env.MODULE_HEARTBEAT_TTL_SEC, 90)
};
