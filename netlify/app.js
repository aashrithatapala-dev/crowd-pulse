/**
 * GodavariPro CrowdPulse — static Firebase dashboard
 * Replaces Flask routes: /data, /history, /firebase/status
 * Uses onValue listeners (no polling).
 */
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import {
  getDatabase,
  ref,
  onValue,
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-database.js";
import { firebaseConfig, MAX_CAPACITY } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

const prevValues = { entered: null, exited: null, current: null, detected: null };
const historyBuffer = [];

// ── DOM helpers ──────────────────────────────────────────────

function animateValue(id, newVal) {
  const el = document.getElementById(id);
  if (!el || prevValues[id] === newVal) return;
  el.classList.remove("bump", "glow");
  void el.offsetWidth;
  el.classList.add("bump", "glow");
  el.textContent = newVal;
  prevValues[id] = newVal;
}

function setConnection(connected, label) {
  document.getElementById("conn-dot").className = connected ? "conn-dot" : "conn-dot error";
  document.getElementById("conn-label").textContent = label;
  document.getElementById("data-source").textContent = connected
    ? "Firebase Realtime"
    : "Disconnected";
}

function updateDashboard(data) {
  if (!data) return;

  animateValue("entered", data.entered ?? 0);
  animateValue("exited", data.exited ?? 0);
  animateValue("current", data.current ?? 0);
  animateValue("detected", data.detected ?? 0);

  const rawStatus = data.status || "No Data";
  const banner = document.getElementById("status-banner");
  const statusText = document.getElementById("status-text");
  const statusIcon = document.getElementById("status-icon");

  if (rawStatus.toLowerCase().includes("overcrowd")) {
    banner.className = "overcrowded";
    statusText.style.color = "var(--red)";
    statusText.textContent = "OVERCROWDED";
    statusIcon.textContent = "🚨";
  } else if (rawStatus.toLowerCase().includes("safe")) {
    banner.className = "safe";
    statusText.style.color = "var(--green)";
    statusText.textContent = "SAFE";
    statusIcon.textContent = "✅";
  } else {
    banner.className = "";
    statusText.style.color = "var(--muted)";
    statusText.textContent = rawStatus;
    statusIcon.textContent = "⏳";
  }

  document.getElementById("ghat-name").textContent = data.ghat || "—";

  const current = data.current ?? 0;
  const pct = Math.min(Math.round((current / MAX_CAPACITY) * 100), 100);
  document.getElementById("capacity-pct").textContent = `${pct}%`;
  const bar = document.getElementById("progress-bar");
  bar.style.width = `${pct}%`;
  bar.className = pct >= 100 ? "danger" : pct >= 75 ? "warning" : "";

  document.getElementById("time").textContent = data.timestamp || "—";
}

function renderHistory() {
  const list = document.getElementById("history-list");
  if (!list) return;

  list.innerHTML = historyBuffer
    .slice(0, 10)
    .map((item) => {
      const isSafe = (item.status || "").toLowerCase().includes("safe");
      return `<div class="history-item">
        <span class="time">${item.timestamp || "—"} · ${item.ghat || "Ghat"}</span>
        <span>👥 ${item.current ?? 0} · <span class="${isSafe ? "status-safe" : "status-danger"}">${item.status || "—"}</span></span>
      </div>`;
    })
    .join("");
}

// ── /data  →  listen to /latest ─────────────────────────────

const latestRef = ref(database, "latest");

onValue(
  latestRef,
  (snapshot) => {
    const data = snapshot.val();
    if (data) {
      updateDashboard(data);
      setConnection(true, "Firebase Live");
    } else {
      document.getElementById("status-text").textContent = "Waiting for detector...";
      setConnection(true, "Connected (no data yet)");
    }
  },
  (error) => {
    console.error("Firebase /latest error:", error);
    document.getElementById("status-text").textContent = "Firebase connection error";
    setConnection(false, "Disconnected");
  }
);

// ── /history  →  listen to /readings ──────────────────────────

const readingsRef = ref(database, "readings");

onValue(readingsRef, (snapshot) => {
  const readings = snapshot.val();
  if (!readings) return;

  historyBuffer.length = 0;

  const dates = Object.keys(readings).sort().reverse();
  for (const date of dates) {
    const times = Object.keys(readings[date]).sort().reverse();
    for (const time of times) {
      historyBuffer.push(readings[date][time]);
      if (historyBuffer.length >= 100) break;
    }
    if (historyBuffer.length >= 100) break;
  }

  renderHistory();
});

// ── /firebase/status  →  .info/connected ─────────────────────

const connectedRef = ref(database, ".info/connected");

onValue(connectedRef, (snapshot) => {
  const connected = snapshot.val() === true;
  if (!connected) {
    setConnection(false, "Reconnecting...");
    document.getElementById("status-text").textContent = "Reconnecting to Firebase...";
  }
});
