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

// ==================== 5. V0.1 组织架构与人员资质交互中心 ====================
function switchMainTab(tab) {
  const tabs = ["system", "org", "rbac"];
  tabs.forEach(t => {
    const btn = document.getElementById("tabBtn" + t.charAt(0).toUpperCase() + t.slice(1));
    const content = document.getElementById("tabContent" + t.charAt(0).toUpperCase() + t.slice(1));
    if (btn) btn.classList.toggle("active", t === tab);
    if (content) content.style.display = (t === tab) ? "block" : "none";
  });

  if (tab === "org") {
    loadOrganizationData();
  } else if (tab === "rbac") {
    loadRbacData();
  }
}

async function loadOrganizationData() {
  const token = localStorage.getItem("bravio_token");
  const headers = { "Authorization": `Bearer ${token}` };

  try {
    // 1. 获取部门树
    const treeRes = await fetch("/api/v1/org/departments/tree", { headers });
    if (treeRes.ok) {
      const tree = await treeRes.json();
      renderDeptTree(tree);
    }

    // 2. 获取岗位
    const posRes = await fetch("/api/v1/org/positions", { headers });
    if (posRes.ok) {
      const positions = await posRes.json();
      renderPositions(positions);
    }

    // 3. 获取员工及资质状态
    const empRes = await fetch("/api/v1/org/employees", { headers });
    if (empRes.ok) {
      const emps = await empRes.json();
      renderEmployees(emps);
    }

    // 4. 获取资质预警
    const expRes = await fetch("/api/v1/org/certifications/expiring?days=30", { headers });
    if (expRes.ok) {
      const expiring = await expRes.json();
      renderWarningBanner(expiring);
    }
  } catch (err) {
    console.error("Load organization data failed:", err);
  }
}

function renderDeptTree(nodes, indent = 0) {
  const container = document.getElementById("deptTreeContainer");
  if (!nodes || nodes.length === 0) {
    if (indent === 0) container.innerHTML = '<div style="color:var(--text-muted);">暂无部门记录</div>';
    return "";
  }

  let html = "";
  nodes.forEach(node => {
    const paddingLeft = indent * 20;
    const badgeColor = node.iso_process_type === "MANAGEMENT" ? "#8b5cf6" : (node.iso_process_type === "CORE" ? "#3b82f6" : "#10b981");
    html += `
      <div style="padding-left: ${paddingLeft}px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
        <div>
          <span>📁 <strong>${escapeHtml(node.name)}</strong></span>
          <span style="font-size:11px; color:#64748b; margin-left:6px;">(${escapeHtml(node.code)})</span>
        </div>
        <div>
          <span style="font-size:11px; padding:2px 6px; border-radius:4px; background:${badgeColor}15; color:${badgeColor}; font-weight:600;">
            ${node.iso_process_type}
          </span>
          <span style="font-size:12px; color:var(--text-muted); margin-left:8px;">${node.employee_count} 人</span>
        </div>
      </div>
    `;
    if (node.children && node.children.length > 0) {
      html += renderDeptTree(node.children, indent + 1);
    }
  });

  if (indent === 0) {
    container.innerHTML = html;
  }
  return html;
}

function renderPositions(positions) {
  const container = document.getElementById("positionsContainer");
  if (!positions || positions.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted);">暂无岗位记录</div>';
    return;
  }

  let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
  positions.forEach(p => {
    const isCritical = p.is_safety_critical;
    html += `
      <div style="padding: 10px; border: 1px solid var(--border-color); border-radius: 6px; background: ${isCritical ? '#fef2f2' : 'transparent'};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>${escapeHtml(p.title)}</strong>
          ${isCritical ? '<span style="background:#fee2e2; color:#dc2626; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">⚠️ 特殊特性关键工位</span>' : '<span style="font-size:11px; color:#64748b;">常规岗位</span>'}
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
          ${escapeHtml(p.description || "无描述")}
        </div>
        ${p.required_cert_types && p.required_cert_types.length > 0 ? `
          <div style="margin-top:6px; font-size:11px; color:#475569;">
            必需证书: ${p.required_cert_types.map(c => `<code style="background:#e2e8f0; padding:1px 4px; border-radius:3px;">${escapeHtml(c)}</code>`).join(" ")}
          </div>
        ` : ''}
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderEmployees(emps) {
  const tbody = document.getElementById("employeesTbody");
  if (!emps || emps.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="padding:16px; text-align:center; color:var(--text-muted);">暂无员工档案</td></tr>';
    return;
  }

  let html = "";
  emps.forEach(e => {
    const comp = e.competency_status || {};
    let compBadge = '<span style="color:#10b981; font-weight:600;">✓ 资质合规</span>';
    if (comp.is_safety_critical_job) {
      if (!comp.is_compliant) {
        compBadge = '<span style="background:#fee2e2; color:#dc2626; padding:2px 6px; border-radius:4px; font-weight:600;">❌ 资质缺失阻断</span>';
      } else if (comp.warning_cert_types && comp.warning_cert_types.length > 0) {
        compBadge = `<span style="background:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; font-weight:600;" title="${escapeHtml(comp.warning_cert_types.join('; '))}">⚠️ 即将到期(${comp.warning_cert_types.length})</span>`;
      }
    }

    html += `
      <tr style="border-bottom: 1px solid var(--border-color);">
        <td style="padding: 10px; font-family:monospace; font-weight:600;">${escapeHtml(e.employee_no)}</td>
        <td style="padding: 10px;"><strong>${escapeHtml(e.name)}</strong></td>
        <td style="padding: 10px;">${escapeHtml(e.department_name || '-')}</td>
        <td style="padding: 10px;">${escapeHtml(e.job_title || '-')}</td>
        <td style="padding: 10px;">${comp.is_safety_critical_job ? '<span style="color:#dc2626; font-weight:600;">★ 关键安全件</span>' : '<span style="color:#94a3b8;">-</span>'}</td>
        <td style="padding: 10px;">${compBadge}</td>
        <td style="padding: 10px;"><span style="color:#10b981;">● ${escapeHtml(e.status)}</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

function renderWarningBanner(expiring) {
  const banner = document.getElementById("certWarningBanner");
  const title = document.getElementById("warningTitle");
  const subtitle = document.getElementById("warningSubtitle");

  if (!expiring || expiring.length === 0) {
    banner.style.background = "#ecfdf5";
    banner.style.borderColor = "#a7f3d0";
    title.textContent = "全员 ISO 9001 & KBA 资质状态受控良好";
    title.style.color = "#047857";
    subtitle.textContent = "当前关键安全工位（Special Characteristics）人员上岗资质均在有效期内，无30天内到期警报。";
    subtitle.style.color = "#065f46";
  } else {
    banner.style.background = "#fffbeb";
    banner.style.borderColor = "#fde68a";
    title.textContent = `检测到 ${expiring.length} 项 ISO/KBA 资质证书进入30天到期预警窗口！`;
    title.style.color = "#b45309";
    const details = expiring.map(c => `${c.cert_name} (编号: ${c.cert_no}, 剩余 ${c.days_to_expire} 天)`).join("；");
    subtitle.textContent = `为避免审核员查验出现不符合项（Non-Conformity），请及时办理换证或评估：${details}`;
    subtitle.style.color = "#78350f";
  }
}

async function loadRbacData() {
  const token = localStorage.getItem("bravio_token");
  const headers = { "Authorization": `Bearer ${token}` };
  const container = document.getElementById("rolesContainer");

  try {
    const res = await fetch("/api/v1/rbac/roles", { headers });
    if (!res.ok) throw new Error("加载角色矩阵失败");
    const roles = await res.json();

    let html = "";
    roles.forEach(r => {
      html += `
        <div style="border:1px solid var(--border-color); border-radius:8px; padding:16px; background:#fafafa;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="color:var(--text-main); font-size:15px;">${escapeHtml(r.name)}</strong>
            <span style="font-size:11px; padding:2px 6px; border-radius:4px; background:#e0e7ff; color:#4338ca; font-weight:600;">
              ${escapeHtml(r.data_scope)}
            </span>
          </div>
          <div style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">
            代码: <code>${escapeHtml(r.code)}</code><br>
            ${escapeHtml(r.description || "无说明")}
          </div>
          <div style="font-size:12px; font-weight:600; color:#475569; margin-bottom:6px;">关联功能权限 (${(r.permissions || []).length} 项):</div>
          <div style="max-height:100px; overflow-y:auto; font-size:11px; color:#64748b; line-height:1.6;">
            ${(r.permissions || []).map(p => `• ${escapeHtml(p.name)} (<code>${escapeHtml(p.code)}</code>)`).join("<br>")}
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color:#dc2626;">${err.message}</div>`;
  }
}

