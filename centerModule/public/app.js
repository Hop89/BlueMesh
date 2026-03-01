const rowsEl = document.getElementById("moduleRows");

function formatTime(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function render(modules) {
  rowsEl.innerHTML = "";

  if (!modules.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="6">No modules registered yet.</td>`;
    rowsEl.appendChild(row);
    return;
  }

  for (const module of modules) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${module.alias} <small>${module.moduleId}</small></td>
      <td><span class="pill ${module.status === "online" ? "ok" : "warn"}">${module.status}</span></td>
      <td>${module.zone || "-"}</td>
      <td>${module.clientCount ?? 0}</td>
      <td>${formatTime(module.lastHeartbeatAt)}</td>
      <td>${module.firmwareVersion || "-"}</td>
    `;
    rowsEl.appendChild(row);
  }
}

async function refresh() {
  const res = await fetch("/api/modules");
  const data = await res.json();
  render(data.modules || []);
}

refresh();
setInterval(refresh, 5000);
