// Bravio ERP - Frontend Logic & Developer Live Logger
let currentLogLevelFilter = null;
let logPollTimer = null;
let healthPollTimer = null;

// ==================== 1. 初始化与视图切换 ====================
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("bravio_token");
  if (token) {
    verifySession(token);
  } else {
    showAuthView();
  }

  // 绑定表单事件
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", handleLogin);
  }
});

function showAuthView() {
  document.getElementById("authView").style.display = "flex";
  document.getElementById("dashboardView").style.display = "none";
  stopPolling();
}

function showDashboardView(user) {
  document.getElementById("authView").style.display = "none";
  document.getElementById("dashboardView").style.display = "flex";

  if (user) {
    document.getElementById("userName").textContent = user.full_name || user.username;
    document.getElementById("userRole").textContent = (user.role || "USER").toUpperCase();
    document.getElementById("userAvatar").textContent = (user.full_name || user.username)[0].toUpperCase();
  }

  // 启动后台轮询探针与实时开发者日志流
  fetchHealth();
  refreshLogs();
  startPolling();
}

// ==================== 2. 快捷凭据与登录逻辑 ====================
function fillCredentials(username, password) {
  document.getElementById("username").value = username;
  document.getElementById("password").value = password;
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const alertEl = document.getElementById("authAlert");
  const loginBtn = document.getElementById("loginBtn");
  const loginBtnText = document.getElementById("loginBtnText");

  alertEl.className = "auth-alert";
  alertEl.textContent = "";
  loginBtn.disabled = true;
  loginBtnText.textContent = "正在验证凭据并建立加密会话...";

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || "登录失败，请检查账号密码");
    }

    // 保存认证 Token
    localStorage.setItem("bravio_token", data.token.access_token);
    localStorage.setItem("bravio_user", JSON.stringify(data.user));

    showDashboardView(data.user);
  } catch (err) {
    alertEl.className = "auth-alert error";
    alertEl.textContent = err.message;
  } finally {
    loginBtn.disabled = false;
    loginBtnText.textContent = "安全登入系统";
  }
}

async function verifySession(token) {
  try {
    const res = await fetch("/api/v1/auth/me", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) {
      const user = await res.json();
      showDashboardView(user);
    } else {
      localStorage.removeItem("bravio_token");
      showAuthView();
    }
  } catch (err) {
    console.error("Session verification error:", err);
    showAuthView();
  }
}

async function handleLogout() {
  const token = localStorage.getItem("bravio_token");
  if (token) {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (e) {
      // 忽略登出请求网络错误
    }
  }
  localStorage.removeItem("bravio_token");
  localStorage.removeItem("bravio_user");
  showAuthView();
}

// ==================== 3. 系统健康探针 ====================
async function fetchHealth() {
  try {
    const res = await fetch("/api/v1/system/health");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("statHealthStatus").textContent = data.status === "operational" ? "正常运行" : "轻微告警";
      document.getElementById("statDbStatus").textContent = data.database === "connected" ? "已连接 (ACID)" : data.database;
      document.getElementById("statUptime").textContent = `${data.uptime_seconds} 秒`;
      document.getElementById("statVersion").textContent = `v${data.version}`;
      
      const navStatusText = document.getElementById("navStatusText");
      if (navStatusText) {
        navStatusText.textContent = `系统正常 (${data.database})`;
      }
    }
  } catch (err) {
    console.error("Health probe error:", err);
  }
}

// ==================== 4. 开发者日志系统 (Live Stream) ====================
async function refreshLogs() {
  try {
    let url = "/api/v1/system/logs?limit=80";
    if (currentLogLevelFilter) {
      url += `&level=${encodeURIComponent(currentLogLevelFilter)}`;
    }
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      renderLogs(data.logs);
    }
  } catch (err) {
    console.error("Fetch dev logs failed:", err);
  }
}

function renderLogs(logs) {
  const container = document.getElementById("logsContainer");
  if (!container) return;

  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="log-line"><span class="log-time">[暂无日志]</span><span class="log-msg">当前过滤条件下未产生新日志</span></div>';
    return;
  }

  let html = "";
  logs.forEach(log => {
    html += `
      <div class="log-line">
        <span class="log-time">${log.timestamp}</span>
        <span class="log-level level-${log.level}">${log.level}</span>
        <span class="log-loc">[${log.module}:${log.line}]</span>
        <span class="log-msg">${escapeHtml(log.message)}</span>
      </div>
    `;
  });

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

function filterLogs(level) {
  currentLogLevelFilter = level;
  const buttons = {
    null: "filterAll",
    "INFO": "filterInfo",
    "WARNING": "filterWarn",
    "ERROR": "filterError"
  };

  Object.values(buttons).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
  });

  const activeId = buttons[level];
  if (activeId) {
    document.getElementById(activeId).classList.add("active");
  }

  refreshLogs();
}

async function triggerTestLog(level, message) {
  try {
    await fetch(`/api/v1/system/logs/test?level=${encodeURIComponent(level)}&message=${encodeURIComponent(message)}`, {
      method: "POST"
    });
    // 立即刷新
    setTimeout(refreshLogs, 150);
  } catch (err) {
    console.error("Trigger test log failed:", err);
  }
}

function clearLocalLogs() {
  const container = document.getElementById("logsContainer");
  if (container) {
    container.innerHTML = '<div class="log-line"><span class="log-time">[已清屏]</span><span class="log-msg">等待新的系统运行时日志流入...</span></div>';
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[m]));
}

function startPolling() {
  stopPolling();
  // 每 3 秒拉取最新开发者日志
  logPollTimer = setInterval(refreshLogs, 3000);
  // 每 5 秒探针一次系统健康
  healthPollTimer = setInterval(fetchHealth, 5000);
}

function stopPolling() {
  if (logPollTimer) clearInterval(logPollTimer);
  if (healthPollTimer) clearInterval(healthPollTimer);
}
