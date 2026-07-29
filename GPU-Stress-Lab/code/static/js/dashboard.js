/* Dashboard 只负责展示，数据和压力测试生命周期由 Flask API 管理。 */
const chartConfig = (label, color, unit) => ({
  type: "line",
  data: { labels: [], datasets: [{ label, data: [], borderColor: color, backgroundColor: `${color}22`, tension: .25, fill: true, pointRadius: 0 }] },
  options: { animation: false, responsive: true, maintainAspectRatio: false, scales: {
    x: { ticks: { color: "#8b949e", maxTicksLimit: 6 }, grid: { color: "#30363d" } },
    y: { beginAtZero: true, title: { display: true, text: unit, color: "#8b949e" }, ticks: { color: "#8b949e" }, grid: { color: "#30363d" } },
  }, plugins: { legend: { labels: { color: "#e6edf3" } } } },
});

const charts = {
  util: new Chart(document.getElementById("util-chart"), chartConfig("利用率", "#58a6ff", "%")),
  temp: new Chart(document.getElementById("temp-chart"), chartConfig("温度", "#f0883e", "°C")),
  memory: new Chart(document.getElementById("memory-chart"), chartConfig("显存", "#a371f7", "MiB")),
};

const text = (id, value) => { document.getElementById(id).textContent = value ?? "--"; };
const number = (value, suffix = "") => value === null || value === undefined ? "--" : `${Number(value).toFixed(1)}${suffix}`;
const formatClock = (value) => {
  const date = new Date((typeof value === "number" ? value * 1000 : value));
  return Number.isNaN(date.getTime()) ? "--:--:--" : date.toLocaleTimeString("en-GB", { hour12: false });
};
const formatDuration = (value) => value === null || value === undefined ? "--" : `${Number(value).toFixed(2)}s`;

function updateChart(chart, history, field, suffix = "") {
  chart.data.labels = history.map(item => formatClock(item.timestamp));
  chart.data.datasets[0].data = history.map(item => item[field]);
  chart.data.datasets[0].label = chart.data.datasets[0].label.replace(/ \(.+\)$/, "") + (suffix ? ` (${suffix})` : "");
  chart.update("none");
}

function updateTestHistory(records) {
  const body = document.getElementById("test-history");
  if (!records.length) {
    body.innerHTML = `<tr><td colspan="6" class="muted">暂无测试记录</td></tr>`;
    return;
  }
  body.innerHTML = records.slice().reverse().map(record => {
    const statusClass = record.status === "PASS" ? "ok" : "warn";
    return `<tr><td>${formatClock(record.test_time)}</td><td>${formatDuration(record.duration_seconds)}</td><td>${number(record.average_utilization, "%")}</td><td>${number(record.peak_temperature, "°C")}</td><td>${number(record.peak_memory, " MiB")}</td><td><span class="badge ${statusClass}">${record.status}</span></td></tr>`;
  }).join("");
}

function updateSummary(summary) {
  const panel = document.getElementById("stress-summary");
  if (!summary) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  text("summary-duration", formatDuration(summary.duration_seconds));
  text("summary-average", number(summary.average_utilization, "%"));
  text("summary-temperature", number(summary.peak_temperature, "°C"));
  text("summary-memory", number(summary.peak_memory, " MiB"));
  text("summary-result", summary.status || "WARNING");
  const badge = document.getElementById("summary-status");
  badge.textContent = summary.status || "WARNING";
  badge.className = `badge ${summary.status === "PASS" ? "ok" : "warn"}`;
}

function updateAlerts(alerts) {
  const root = document.getElementById("alerts");
  document.getElementById("alert-count").textContent = alerts.length;
  document.getElementById("alert-count").className = `badge ${alerts.length ? "warn" : "ok"}`;
  root.innerHTML = alerts.length ? alerts.map(alert => `<div class="warning-item"><strong>${alert.level}</strong> · ${alert.message}</div>`).join("") : `<p class="muted">暂无异常</p>`;
}

function updateStatus(payload) {
  const gpu = payload.gpu;
  const history = payload.history || [];
  const stress = payload.stress || {};
  const connection = document.getElementById("connection");
  connection.textContent = payload.error ? "采集异常" : "已连接";
  connection.className = `badge ${payload.error ? "error" : "ok"}`;
  if (gpu) {
    text("gpu-name", gpu.name);
    text("gpu-util", number(gpu.utilization_percent, "%"));
    text("gpu-memory", `${number(gpu.memory_used_mib)} / ${number(gpu.memory_total_mib)} MiB`);
    text("gpu-temp", number(gpu.temperature_c, "°C"));
    text("gpu-power", number(gpu.power_draw_w, "W"));
    text("gpu-version", `${gpu.driver_version || "--"} / ${gpu.cuda_version || "--"}`);
  }
  updateChart(charts.util, history, "utilization_percent", "%");
  updateChart(charts.temp, history, "temperature_c", "°C");
  updateChart(charts.memory, history, "memory_used_mib", "MiB");
  const stressBadge = document.getElementById("stress-status");
  stressBadge.textContent = stress.running ? "运行中" : "未运行";
  stressBadge.className = `badge ${stress.running ? "ok" : "muted"}`;
  document.getElementById("stress-meta").textContent = stress.running ? `已运行 ${Math.max(0, Math.floor(Date.now() / 1000 - stress.started_at))} 秒 · ${stress.size} x ${stress.size}` : (stress.error || (stress.summary ? `测试完成于 ${formatClock(stress.summary.completed_at)}` : "等待测试"));
  updateSummary(stress.summary);
  updateTestHistory(payload.test_history || []);
  updateAlerts(payload.alerts || []);
}

async function refresh() {
  try {
    const [statusResponse, historyResponse] = await Promise.all([fetch("/api/status"), fetch("/api/history")]);
    const status = await statusResponse.json();
    const history = await historyResponse.json();
    updateStatus({ ...status, test_history: history.records || [] });
  }
  catch (error) { document.getElementById("connection").textContent = "连接失败"; document.getElementById("connection").className = "badge error"; }
}

async function post(path, body = {}) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "请求失败");
  return result;
}

document.getElementById("start-stress").addEventListener("click", async () => {
  try { await post("/api/stress/start", { duration: Number(document.getElementById("duration").value), size: Number(document.getElementById("size").value), interval: 1 }); refresh(); }
  catch (error) { window.alert(error.message); }
});
document.getElementById("stop-stress").addEventListener("click", async () => {
  try { await post("/api/stress/stop"); refresh(); }
  catch (error) { window.alert(error.message); }
});
refresh();
setInterval(refresh, 1000);
