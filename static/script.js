const SOURCE_API = "http://127.0.0.1:3001/api/data";
const EXPORT_API = "http://127.0.0.1:8000/api/export";

let tableData = [];
let columns = [];
let headerNames = [];
let dragColIdx = null;

// --- Toast Notifications
function showToastNotification(msg, type = "success", dur = 3700) {
  const area = document.getElementById("notifications-area");
  const notif = document.createElement("div");
  notif.className = "toast-notif " + type;
  notif.innerHTML = `<span>${msg}</span><button class="toast-close" title="Dismiss">&times;</button>`;
  area.appendChild(notif);
  setTimeout(() => (notif.style.opacity = 1), 60);
  notif.querySelector(".toast-close").onclick = () => removeToast(notif);
  setTimeout(() => removeToast(notif), dur);
}
function removeToast(notif) {
  notif.style.animation = "toast-out 0.4s forwards";
  setTimeout(() => notif.remove(), 390);
}

// --- 1. Fetch table preview ---
document.getElementById("fetch-table-btn").onclick = async () => {
  try {
    const resp = await fetch(SOURCE_API);
    const data = await resp.json();
    if (!Array.isArray(data) || !data.length) throw new Error("Empty data");
    tableData = data;
    columns = Object.keys(tableData[0]);
    headerNames = [...columns];
    renderTable();
    showToastNotification("Table fetched!", "success");
  } catch (e) {
    showToastNotification(
      "Fetch failed: " + (e.message || "Unknown error"),
      "error",
    );
  }
};

function renderTable() {
  const container = document.getElementById("table-container");
  if (!columns.length) {
    container.innerHTML = `<table><thead><tr>${[1, 2, 3].map(() => "<th>—</th>").join("")}</tr></thead>
      <tbody><tr><td>—</td><td>—</td><td>—</td></tr></tbody></table>`;
    return;
  }
  // Table header with drag and rename
  let thead = "<thead><tr>";
  headerNames.forEach((name, i) => {
    thead += `<th draggable="true" data-idx="${i}">
      <input class="header-edit" type="text" value="${name}" data-idx="${i}" title="Rename column"/>
    </th>`;
  });
  thead += "</tr></thead>";
  // Table body
  let tbody = "<tbody>";
  for (const row of tableData.slice(0, 7)) {
    tbody += "<tr>";
    headerNames.forEach((name) => {
      // Find the original column for this header name
      const origCol = columns[headerNames.indexOf(name)] || name;
      tbody += `<td>${row[origCol] !== undefined ? row[origCol] : ""}</td>`;
    });
    tbody += "</tr>";
  }
  tbody += "</tbody>";
  container.innerHTML = `<table>${thead}${tbody}</table>`;

  // Attach drag and drop events
  container.querySelectorAll("th").forEach((th) => {
    const idx = +th.dataset.idx;
    th.ondragstart = (e) => {
      dragColIdx = idx;
      th.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    };
    th.ondragover = (e) => {
      e.preventDefault();
      if (dragColIdx !== null && dragColIdx !== idx)
        th.classList.add("drag-over");
    };
    th.ondragleave = () => th.classList.remove("drag-over");
    th.ondrop = (e) => {
      e.preventDefault();
      if (dragColIdx === null || dragColIdx === idx) return;
      // Reorder headerNames
      const moved = headerNames.splice(dragColIdx, 1)[0];
      headerNames.splice(idx, 0, moved);
      dragColIdx = null;
      renderTable();
    };
    th.ondragend = () => {
      th.classList.remove("dragging");
      container
        .querySelectorAll("th")
        .forEach((t) => t.classList.remove("drag-over"));
      dragColIdx = null;
    };
    // Inline rename
    th.querySelector("input").oninput = (e) => {
      headerNames[idx] = e.target.value;
      // Optionally: live update mapping on rename
    };
  });
}

// --- 2. Save mapping (auto on reorder/rename) ---
async function saveColumnMapping() {
  if (!columns.length)
    return showToastNotification("No columns to save.", "error");
  // headerNames: current order and user names, columns: original order
  const mapping = headerNames.map((name, idx) => ({
    name,
    column: columns.indexOf(headerNames[idx]),
    change_order: idx,
  }));
  try {
    const res = await fetch(`${EXPORT_API}/bulk-inputs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mapping),
    });
    if (!res.ok) throw new Error("Bulk inputs failed");
    showToastNotification("Column mapping saved.", "success");
  } catch {
    showToastNotification("Failed to save mapping.", "error");
  }
}

// Save mapping before processing or config
["set-config-btn", "start-task-btn"].forEach((id) => {
  document.getElementById(id).addEventListener("click", saveColumnMapping);
});

// --- 3. Export config ---
document.getElementById("set-config-btn").onclick = async () => {
  const config = {
    file_type: document.getElementById("file-type").value,
    page_limit: Number(document.getElementById("page-limit").value),
    rate_limit: Number(document.getElementById("rate-limit").value) || null,
    tmp_dir: document.getElementById("tmp-dir").value || null,
    db_url: SOURCE_API,
  };
  try {
    const res = await fetch(`${EXPORT_API}/configure`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("Config failed");
    showToastNotification("Config set.", "success");
  } catch {
    showToastNotification("Failed to set config.", "error");
  }
};

// --- 4. Start, monitor, download ---
document.getElementById("start-task-btn").onclick = async () => {
  try {
    const res = await fetch(`${EXPORT_API}/start`, { method: "POST" });
    const data = await res.json();
    if (!data.task_id) throw new Error("No task_id");
    showToastNotification(`Task ${data.task_id} started.`, "success");
    pollStatus(data.task_id);
  } catch (e) {
    showToastNotification("Start failed: " + (e.message || "Unknown"), "error");
  }
};

function pollStatus(taskId) {
  const statusDiv = document.getElementById("task-status");
  statusDiv.innerHTML = `<div>Task <b>${taskId}</b> running...</div>`;
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`${EXPORT_API}/status/${taskId}`);
      const data = await res.json();
      statusDiv.innerHTML = `
        <div>
          Task <b>${taskId}</b> status: <b>${data.status || "unknown"}</b>
          ${data.progress !== undefined ? `(${data.progress}%)` : ""}
          ${data.error ? `<div style="color:#c62828">Error: ${data.error}</div>` : ""}
          ${data.status === "completed" ? `<a href="${EXPORT_API}/download/${taskId}" class="download-link">Download Result</a>` : ""}
        </div>
      `;
      if (["completed", "failed", "cancelled"].includes(data.status))
        clearInterval(interval);
    } catch {
      clearInterval(interval);
      statusDiv.innerHTML += `<div style="color:#c62828">Status fetch failed.</div>`;
    }
  }, 2000);
}

// On load, blank table
window.addEventListener("DOMContentLoaded", () => {
  columns = ["col1", "col2", "col3"];
  headerNames = [...columns];
  renderTable();
});
