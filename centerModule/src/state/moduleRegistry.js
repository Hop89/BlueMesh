const modules = new Map();

export const moduleRegistry = {
  list() {
    return Array.from(modules.values()).sort((a, b) => a.moduleId.localeCompare(b.moduleId));
  },

  upsert(data) {
    const now = new Date().toISOString();
    const existing = modules.get(data.moduleId);

    const record = {
      moduleId: data.moduleId,
      alias: data.alias || existing?.alias || data.moduleId,
      zone: data.zone || existing?.zone || "unassigned",
      status: data.status || existing?.status || "provisioning",
      backhaulSsid: data.backhaulSsid || existing?.backhaulSsid || null,
      clientCount: data.clientCount ?? existing?.clientCount ?? 0,
      firmwareVersion: data.firmwareVersion || existing?.firmwareVersion || "unknown",
      lastHeartbeatAt: data.lastHeartbeatAt || existing?.lastHeartbeatAt || null,
      createdAt: existing?.createdAt || now,
      updatedAt: now
    };

    modules.set(data.moduleId, record);
    return record;
  },

  heartbeat(moduleId, payload = {}) {
    const existing = modules.get(moduleId);
    if (!existing) {
      return null;
    }

    const now = new Date().toISOString();
    const updated = {
      ...existing,
      status: payload.status || "online",
      clientCount: payload.clientCount ?? existing.clientCount,
      backhaulRssi: payload.backhaulRssi ?? existing.backhaulRssi ?? null,
      lastHeartbeatAt: now,
      updatedAt: now
    };

    modules.set(moduleId, updated);
    return updated;
  }
};
