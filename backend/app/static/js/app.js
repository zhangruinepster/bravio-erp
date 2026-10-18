// Bravio ERP - Odoo 架构企业级交互中枢与人力资源管理 (docs/02, docs/03, docs/04)

let currentUser = null;
let currentApp = "hr";             // 当前活动 App: 'hr', 'mes', 'system'
let currentViewMode = "list";       // 视图模式: 'list', 'kanban'
let employeeFilterStatus = "ALL";   // 员工过滤状态
let employeeSearchQuery = "";       // 搜索关键词
let cachedEmployees = [];           // 本地缓存的员工数据
let cachedDepartments = [];         // 本地缓存的部门数据
let cachedPositions = [];           // 本地缓存的岗位体系
let cachedRoles = [];               // 本地缓存的角色清单
let cachedPermissions = [];         // 本地缓存的权限字典

let logPollTimer = null;
let healthPollTimer = null;
let currentLogLevelFilter = null;

// ==================== 1. 初始化与登录会话 ====================
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("bravio_token");
  if (token) {
    verifySession(token);
  } else {
    showAuthView();
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", handleLogin);
  }
});

function showAuthView() {
  document.getElementById("authView").style.display = "flex";
  document.getElementById("dashboardView").style.display = "none";
  closeAppSwitcher();
  stopPolling();
}

function showDashboardView(user) {
  currentUser = user;
  document.getElementById("authView").style.display = "none";
  document.getElementById("dashboardView").style.display = "flex";

  // 1. 渲染用户个人信息与角色职位
  const displayName = user.full_name || user.username;
  document.getElementById("userName").textContent = displayName;
  document.getElementById("userAvatar").textContent = displayName[0].toUpperCase();

  let roleLabel = "OPERATOR";
  if (user.is_superuser || user.role === "admin") {
    roleLabel = "超级管理员";
  } else if (user.username === "gm") {
    roleLabel = "集团总经理";
  } else if (user.username === "pe") {
    roleLabel = "产品工程师";
  } else if (user.username === "qe") {
    roleLabel = "质量工程师";
  } else if (user.username === "supplier") {
    roleLabel = "供应商账户";
  } else if (user.roles && user.roles.length > 0) {
    roleLabel = user.roles[0].name;
  }
  document.getElementById("userRole").textContent = roleLabel;

  // 2. 角色与权限视图隔离 (核心安全规范 - 仅系统总管理员可见运维控制台与日志流)
  // 总经理(gm) 与 其他业务人员严禁访问系统运维控制台与日志！
  const isAdmin = Boolean(user.is_superuser || user.role === "admin");
  const appTileSystem = document.getElementById("appTileSystem");
  if (appTileSystem) {
    appTileSystem.style.display = isAdmin ? "flex" : "none";
  }

  // 3. 针对不同角色引导进入默认应用
  if (isAdmin) {
    selectApp("hr"); // 管理员默认进入 HR 人事与组织中枢
    fetchHealth();
    refreshLogs();
    startPolling();
  } else {
    // 严格阻断非管理员的系统日志后台轮询
    stopPolling();
    selectApp("hr");
  }

  // 预载人事基础字典
  loadOrganizationData();
  loadRolesAndPermissions();
}

function fillCredentials(username, password, autoLogin = false) {
  document.getElementById("username").value = username;
  document.getElementById("password").value = password;
  if (autoLogin) {
    const fakeEvent = { preventDefault: () => {} };
    handleLogin(fakeEvent);
  }
}

// 顶部快捷测试角色切换下拉菜单
function toggleRoleSwitchDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("quickRoleDropdown");
  if (!dropdown) return;
  const isHidden = dropdown.style.display === "none" || !dropdown.style.display;
  dropdown.style.display = isHidden ? "block" : "none";
}

// 点击网页空白区域自动关闭下拉框
document.addEventListener("click", () => {
  const dropdown = document.getElementById("quickRoleDropdown");
  if (dropdown) dropdown.style.display = "none";
});

// 免登出快速切换测试账号
async function quickSwitchUser(username, password) {
  const dropdown = document.getElementById("quickRoleDropdown");
  if (dropdown) dropdown.style.display = "none";

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) {
      alert("切换失败: " + (data.detail || data.message || "登录错误"));
      return;
    }

    localStorage.setItem("bravio_token", data.token.access_token);
    localStorage.setItem("bravio_user", JSON.stringify(data.user));
    showDashboardView(data.user);

    // 提示快速切换成功
    const alertBanner = document.createElement("div");
    alertBanner.style.position = "fixed";
    alertBanner.style.top = "60px";
    alertBanner.style.right = "24px";
    alertBanner.style.background = "#10b981";
    alertBanner.style.color = "#ffffff";
    alertBanner.style.padding = "10px 18px";
    alertBanner.style.borderRadius = "8px";
    alertBanner.style.boxShadow = "0 10px 25px -5px rgba(0,0,0,0.2)";
    alertBanner.style.fontSize = "13px";
    alertBanner.style.fontWeight = "600";
    alertBanner.style.zIndex = "9999";
    alertBanner.textContent = `⚡ 已无缝切换到测试账号: ${data.user.full_name || data.user.username} (${data.user.username})`;
    document.body.appendChild(alertBanner);
    setTimeout(() => alertBanner.remove(), 2500);

  } catch (err) {
    alert("切换失败: " + err.message);
  }
}

async function handleLogin(e) {
  if (e && e.preventDefault) e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const alertEl = document.getElementById("authAlert");
  const loginBtn = document.getElementById("loginBtn");
  const loginBtnText = document.getElementById("loginBtnText");

  alertEl.className = "auth-alert";
  alertEl.textContent = "";
  loginBtn.disabled = true;
  loginBtnText.textContent = "正在建立安全加密会话...";

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
    localStorage.removeItem("bravio_token");
    showAuthView();
  }
}

function handleLogout() {
  localStorage.removeItem("bravio_token");
  localStorage.removeItem("bravio_user");
  showAuthView();
}

// ==================== 2. Odoo 架构: App Switcher 应用切换 ====================
function toggleAppSwitcher() {
  const modal = document.getElementById("appSwitcherModal");
  modal.style.display = (modal.style.display === "none" || !modal.style.display) ? "flex" : "none";
}

function closeAppSwitcher(e) {
  const modal = document.getElementById("appSwitcherModal");
  if (modal) modal.style.display = "none";
}

function selectApp(appName) {
  currentApp = appName;
  closeAppSwitcher();

  const appViewHr = document.getElementById("appViewHr");
  const appViewSystem = document.getElementById("appViewSystem");
  const appViewMes = document.getElementById("appViewMes");
  const navTitle = document.getElementById("navCurrentAppTitle");
  const navSub = document.getElementById("navSubBreadcrumb");

  appViewHr.style.display = "none";
  appViewSystem.style.display = "none";
  appViewMes.style.display = "none";

  if (appName === "hr") {
    appViewHr.style.display = "block";
    navTitle.textContent = "👥 人力资源与组织架构";
    navSub.textContent = "/ 员工档案";
    loadOrganizationData();
  } else if (appName === "system") {
    // 安全阻断：总经理与普通业务人员严禁进入系统运维控制台
    const isAdmin = currentUser && (currentUser.is_superuser || currentUser.role === "admin");
    if (!isAdmin) {
      if (currentUser && currentUser.username === "gm") {
        alert("【安全合规隔离】陈总裁（集团总经理）拥有全企业业务模块最高管辖权，但遵循安全最小化与审计合规原则，严禁访问底层系统运维控制台与开发者日志！");
      } else {
        alert("【安全阻断】您当前的角色不具备底层系统运维控制台的访问权限！");
      }
      selectApp("hr");
      return;
    }
    appViewSystem.style.display = "block";
    navTitle.textContent = "🛠️ 系统运维控制台";
    navSub.textContent = "/ 实时开发者日志";
    refreshLogs();
    fetchHealth();
  } else if (appName === "mes") {
    appViewMes.style.display = "block";
    navTitle.textContent = "🏭 车间与制造协同";
    navSub.textContent = "/ 业务执行工作台";

    if (currentUser) {
      const uName = currentUser.username;
      const fName = currentUser.full_name || currentUser.username;
      const mesNameEl = document.getElementById("mesOperatorName");
      const mesMetaEl = document.getElementById("mesOperatorMeta");
      const mesBadgeEl = document.getElementById("mesOperatorBadge");
      const mesIconEl = document.getElementById("mesUserIcon");
      const mesTaskEl = document.getElementById("mesTaskSummary");

      if (uName === "gm") {
        if (mesIconEl) mesIconEl.textContent = "👔";
        if (mesNameEl) mesNameEl.textContent = `${fName} (集团总经理)`;
        if (mesMetaEl) mesMetaEl.textContent = "所属部门：Bravio 集团总部 · 统管全企业各业务中心 (严禁访问系统运维与日志)";
        if (mesBadgeEl) mesBadgeEl.textContent = "★ 企业最高经营管理授权 (全业务数据流可达)";
        if (mesTaskEl) mesTaskEl.textContent = "经营视角：正在监控制造中心、质保中心与研发中心的协同推进。系统后台运维与日志受安全合规审计隔离。";
      } else if (uName === "pe") {
        if (mesIconEl) mesIconEl.textContent = "📐";
        if (mesNameEl) mesNameEl.textContent = `${fName} (产品工程师)`;
        if (mesMetaEl) mesMetaEl.textContent = "所属部门：研发与工程技术中心 · 岗位：产品研发与硬件工程主管";
        if (mesBadgeEl) mesBadgeEl.textContent = "✓ 产品物料与BOM研发工程师资质";
        if (mesTaskEl) mesTaskEl.textContent = "研发待办：配合稍后版本中的【产品模组与BOM】进行硬件图号主数据、工程物料清单维护。";
      } else if (uName === "qe") {
        if (mesIconEl) mesIconEl.textContent = "🛡️";
        if (mesNameEl) mesNameEl.textContent = `${fName} (质量工程师)`;
        if (mesMetaEl) mesMetaEl.textContent = "所属部门：质量保证与法规合规中心 · 岗位：汽车特殊特性与首件质量工程师";
        if (mesBadgeEl) mesBadgeEl.textContent = "✓ 具有汽车特殊特性(SC/CC)质检与德国KBA一致性审查资质";
        if (mesTaskEl) mesTaskEl.textContent = "质保待办：配合稍后版本中的【质量工程师与8D客诉】进行进料抽检、首件放行与生产一致性审查。";
      } else if (uName === "supplier") {
        if (mesIconEl) mesIconEl.textContent = "🏭";
        if (mesNameEl) mesNameEl.textContent = `${fName} (供应商专员)`;
        if (mesMetaEl) mesMetaEl.textContent = "所属部门：先进制造与供应链中心 · 岗位：供应链采购与外协制造主管";
        if (mesBadgeEl) mesBadgeEl.textContent = "✓ 供应商协同与外协制造交接权限";
        if (mesTaskEl) mesTaskEl.textContent = "供应链待办：配合稍后版本中的【供应商外协制造】进行批次送货确认、外协加工进度跟踪。";
      } else {
        if (mesIconEl) mesIconEl.textContent = "🔑";
        if (mesNameEl) mesNameEl.textContent = `${fName} (系统总管理员)`;
        if (mesMetaEl) mesMetaEl.textContent = "拥有企业底层系统架构与全局数据访问权";
        if (mesBadgeEl) mesBadgeEl.textContent = "✓ 系统最高超级管理员权限 (Superuser)";
        if (mesTaskEl) mesTaskEl.textContent = "运维概况：全系统服务集群健康正常。";
      }
    }
  }
}

// ==================== 3. Odoo 人力资源管理与组织架构 (HR App) ====================
function switchHrSubTab(tab) {
  const tabs = ["employees", "deptTree", "competency", "roles"];
  tabs.forEach(t => {
    const btn = document.getElementById("hrSubNav" + t.charAt(0).toUpperCase() + t.slice(1));
    const panel = document.getElementById("hrPanel" + t.charAt(0).toUpperCase() + t.slice(1));
    if (btn) btn.classList.toggle("active", t === tab);
    if (panel) panel.style.display = (t === tab) ? "block" : "none";
  });

  const navSub = document.getElementById("navSubBreadcrumb");
  const titles = {
    employees: "/ 员工花名册与账号",
    deptTree: "/ 多级组织架构树",
    competency: "/ 关键工位与资质预警",
    roles: "/ 系统角色与权限"
  };
  if (navSub) navSub.textContent = titles[tab] || "";
}

function switchViewMode(mode) {
  currentViewMode = mode;
  document.getElementById("btnViewList").classList.toggle("active", mode === "list");
  document.getElementById("btnViewKanban").classList.toggle("active", mode === "kanban");

  document.getElementById("employeeListView").style.display = (mode === "list") ? "block" : "none";
  document.getElementById("employeeKanbanView").style.display = (mode === "kanban") ? "grid" : "none";
  renderEmployeesView();
}

function handleSearchEmployees(query) {
  employeeSearchQuery = (query || "").trim().toLowerCase();
  renderEmployeesView();
}

function applyEmployeeFilter(status, el) {
  employeeFilterStatus = status;
  document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
  if (el) el.classList.add("active");
  renderEmployeesView();
}

async function loadOrganizationData() {
  const token = localStorage.getItem("bravio_token");
  const headers = { "Authorization": `Bearer ${token}` };

  try {
    // 1. 部门树
    const treeRes = await fetch("/api/v1/org/departments/tree", { headers });
    if (treeRes.ok) {
      cachedDepartments = await treeRes.json();
      renderDeptTree(cachedDepartments);
      populateDeptSelects(cachedDepartments);
    }

    // 2. 岗位
    const posRes = await fetch("/api/v1/org/positions", { headers });
    if (posRes.ok) {
      cachedPositions = await posRes.json();
      renderPositions(cachedPositions);
      populateJobSelect(cachedPositions);
    }

    // 3. 员工
    const empRes = await fetch("/api/v1/org/employees", { headers });
    if (empRes.ok) {
      cachedEmployees = await empRes.json();
      renderEmployeesView();
    }

    // 4. 资质预警
    const expRes = await fetch("/api/v1/org/certifications/expiring?days=30", { headers });
    if (expRes.ok) {
      const expiring = await expRes.json();
      renderWarningBanner(expiring);
      renderExpiringList(expiring);
    }
  } catch (err) {
    console.error("加载组织与人事数据失败:", err);
  }
}

function getFilteredEmployees() {
  return cachedEmployees.filter(e => {
    // 文本搜索
    const matchSearch = !employeeSearchQuery ||
      (e.name && e.name.toLowerCase().includes(employeeSearchQuery)) ||
      (e.employee_no && e.employee_no.toLowerCase().includes(employeeSearchQuery)) ||
      (e.department_name && e.department_name.toLowerCase().includes(employeeSearchQuery)) ||
      (e.job_title && e.job_title.toLowerCase().includes(employeeSearchQuery));

    if (!matchSearch) return false;

    // 状态过滤
    if (employeeFilterStatus === "ACTIVE") {
      return e.status === "ACTIVE";
    }
    if (employeeFilterStatus === "WARNING") {
      const comp = e.competency_status || {};
      return (comp.warning_cert_types && comp.warning_cert_types.length > 0);
    }
    if (employeeFilterStatus === "CRITICAL") {
      const comp = e.competency_status || {};
      return comp.is_safety_critical_job === true;
    }
    return true;
  });
}

function renderEmployeesView() {
  const emps = getFilteredEmployees();

  // 1. 列表渲染
  const tbody = document.getElementById("employeesTbody");
  if (!emps || emps.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="padding:24px; text-align:center; color:var(--text-muted);">未找到符合条件的员工记录</td></tr>';
  } else {
    let listHtml = "";
    emps.forEach(e => {
      const comp = e.competency_status || {};
      let compBadge = '<span style="color:#10b981; font-weight:600;">✓ 资质受控</span>';
      if (comp.is_safety_critical_job) {
        if (!comp.is_compliant) {
          compBadge = '<span style="background:#fee2e2; color:#dc2626; padding:2px 8px; border-radius:4px; font-weight:600;">❌ 缺失阻断</span>';
        } else if (comp.warning_cert_types && comp.warning_cert_types.length > 0) {
          compBadge = `<span style="background:#fef3c7; color:#d97706; padding:2px 8px; border-radius:4px; font-weight:600;" title="${escapeHtml(comp.warning_cert_types.join('; '))}">⚠️ 临期预警(${comp.warning_cert_types.length})</span>`;
        }
      }

      const accInfo = e.account_username ?
        `<span>👤 <strong>${escapeHtml(e.account_username)}</strong></span><br><span style="font-size:11px; color:#64748b;">${escapeHtml(e.account_roles.join(', ') || '常规角色')}</span>` :
        `<span style="color:#94a3b8; font-style:italic;">未开通账号</span>`;

      listHtml += `
        <tr style="border-bottom: 1px solid var(--border-color); hover:background:#f8fafc;">
          <td style="padding: 12px 16px; font-family:monospace; font-weight:700; color:var(--primary);">${escapeHtml(e.employee_no)}</td>
          <td style="padding: 12px 16px;"><strong>${escapeHtml(e.name)}</strong><br><span style="font-size:11px; color:var(--text-muted);">${escapeHtml(e.email)}</span></td>
          <td style="padding: 12px 16px;">${escapeHtml(e.department_name || '-')}</td>
          <td style="padding: 12px 16px;">${escapeHtml(e.job_title || '-')}</td>
          <td style="padding: 12px 16px;">${accInfo}</td>
          <td style="padding: 12px 16px;">${comp.is_safety_critical_job ? '<span style="background:#fee2e2; color:#dc2626; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;">★ 汽车安全关键工位</span>' : '<span style="color:#94a3b8;">-</span>'}</td>
          <td style="padding: 12px 16px;">${compBadge}</td>
          <td style="padding: 12px 16px; text-align:center;">
            <button class="btn-secondary" style="font-size:11px; padding:3px 8px;" onclick="viewEmployeeDetail('${e.id}')">查看档案</button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = listHtml;
  }

  // 2. 看板渲染 (Kanban Cards - docs/02 规范)
  const kanban = document.getElementById("employeeKanbanView");
  if (!emps || emps.length === 0) {
    kanban.innerHTML = '<div style="grid-column: 1 / -1; padding:32px; text-align:center; color:var(--text-muted);">暂无员工看板卡片</div>';
  } else {
    let kanbanHtml = "";
    emps.forEach(e => {
      const comp = e.competency_status || {};
      const avatarChar = (e.name || "U")[0].toUpperCase();
      kanbanHtml += `
        <div class="kanban-card" onclick="viewEmployeeDetail('${e.id}')">
          <div class="kanban-card-header">
            <div class="kanban-avatar">${avatarChar}</div>
            <div style="flex:1; overflow:hidden;">
              <div style="font-weight:700; font-size:15px; color:var(--text-main);">${escapeHtml(e.name)}</div>
              <div style="font-size:11.5px; font-family:monospace; color:var(--primary); font-weight:600;">${escapeHtml(e.employee_no)}</div>
            </div>
            ${comp.is_safety_critical_job ? '<span title="关键安全件" style="color:#dc2626; font-size:18px;">★</span>' : ''}
          </div>
          <div style="font-size:12.5px; color:#475569; line-height:1.6; margin-bottom:12px;">
            <div>🏢 <strong>部门:</strong> ${escapeHtml(e.department_name || '未分配')}</div>
            <div>💼 <strong>岗位:</strong> ${escapeHtml(e.job_title || '未指定')}</div>
            <div>🔐 <strong>系统账号:</strong> ${escapeHtml(e.account_username || '未开通')}</div>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-light); padding-top:10px; font-size:11.5px;">
            <span style="color:#10b981; font-weight:600;">● ${escapeHtml(e.status)}</span>
            <span style="font-weight:600; color:${comp.is_compliant ? '#059669' : '#dc2626'};">${comp.is_compliant ? '✓ 资质合格' : '❌ 资质缺失'}</span>
          </div>
        </div>
      `;
    });
    kanban.innerHTML = kanbanHtml;
  }
}

function viewEmployeeDetail(empId) {
  const emp = cachedEmployees.find(e => e.id === empId);
  if (!emp) return;
  alert(`【员工受控档案】\n工号: ${emp.employee_no}\n姓名: ${emp.name}\n部门: ${emp.department_name || '-'}\n当前岗位: ${emp.job_title || '-'}\n绑定的 ERP 账号: ${emp.account_username || '未开通'}\n资质合规结论: ${emp.competency_status ? emp.competency_status.notes : '正常'}`);
}

// 部门树渲染
function renderDeptTree(nodes, indent = 0) {
  const container = document.getElementById("deptTreeContainer");
  if (!nodes || nodes.length === 0) {
    if (indent === 0) container.innerHTML = '<div style="color:var(--text-muted);">暂无组织部门记录</div>';
    return "";
  }

  let html = "";
  nodes.forEach(node => {
    const paddingLeft = indent * 24;
    const badgeColor = node.iso_process_type === "MANAGEMENT" ? "#8b5cf6" : (node.iso_process_type === "CORE" ? "#3b82f6" : "#10b981");
    html += `
      <div style="padding-left: ${paddingLeft}px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; border-bottom:1px solid var(--border-light); padding-bottom:6px;">
        <div>
          <span>📁 <strong>${escapeHtml(node.name)}</strong></span>
          <span style="font-size:11.5px; color:#64748b; margin-left:6px; font-family:monospace;">(${escapeHtml(node.code)})</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:11px; padding:2px 6px; border-radius:4px; background:${badgeColor}15; color:${badgeColor}; font-weight:600;">
            ISO: ${node.iso_process_type}
          </span>
          <span style="font-size:12px; color:var(--text-muted);">${node.employee_count} 名在职</span>
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

  let html = '<div style="display:flex; flex-direction:column; gap:10px;">';
  positions.forEach(p => {
    html += `
      <div style="padding:12px; border:1px solid var(--border-color); border-radius:6px; background:${p.is_safety_critical ? '#fef2f2' : '#ffffff'};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>${escapeHtml(p.title)}</strong>
          ${p.is_safety_critical ? '<span style="background:#fee2e2; color:#dc2626; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">★ 汽车安全特性工位</span>' : '<span style="font-size:11px; color:#64748b;">常规通用工位</span>'}
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${escapeHtml(p.description || "无说明")}</div>
        ${p.required_cert_types && p.required_cert_types.length > 0 ? `
          <div style="margin-top:6px; font-size:11px; color:#475569;">
            强制持证要求: ${p.required_cert_types.map(c => `<code style="background:#e2e8f0; padding:1px 5px; border-radius:3px;">${escapeHtml(c)}</code>`).join(" ")}
          </div>
        ` : ''}
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderWarningBanner(expiring) {
  const banner = document.getElementById("certWarningBanner");
  const title = document.getElementById("warningTitle");
  const subtitle = document.getElementById("warningSubtitle");

  if (!expiring || expiring.length === 0) {
    banner.style.background = "#ecfdf5";
    banner.style.borderColor = "#a7f3d0";
    title.textContent = "✓ 全员 ISO 9001 & KBA 资质受控状态良好";
    title.style.color = "#047857";
    subtitle.textContent = "所有特殊特性工位人员资质均在有效期内，未发现30天内到期风险。";
    subtitle.style.color = "#065f46";
  } else {
    banner.style.background = "#fffbeb";
    banner.style.borderColor = "#fde68a";
    title.textContent = `⚠️ 检测到 ${expiring.length} 项 ISO/KBA 资质证书进入30天到期预警窗口！`;
    title.style.color = "#b45309";
    const details = expiring.map(c => `${c.cert_name} (编号: ${c.cert_no}, 剩余 ${c.days_to_expire} 天)`).join("；");
    subtitle.textContent = `依据 KBA 生产一致性审查规范，请及时换证或评审：${details}`;
    subtitle.style.color = "#78350f";
  }
}

function renderExpiringList(expiring) {
  const list = document.getElementById("expiringCertsList");
  if (!expiring || expiring.length === 0) {
    list.innerHTML = '<div style="color:#059669; padding:16px 0;">✓ 暂无临期证书，所有资质合规完备。</div>';
    return;
  }

  let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
  expiring.forEach(c => {
    html += `
      <div style="padding:10px 14px; border:1px solid #fde68a; background:#fffbeb; border-radius:6px;">
        <div style="display:flex; justify-content:space-between; font-weight:600; color:#b45309;">
          <span>${escapeHtml(c.cert_name)}</span>
          <span>剩余 ${c.days_to_expire} 天</span>
        </div>
        <div style="font-size:11.5px; color:#78350f; margin-top:4px;">
          证书统一编号: <code>${escapeHtml(c.cert_no)}</code> · 颁发机构: ${escapeHtml(c.issuing_authority)}
        </div>
      </div>
    `;
  });
  html += '</div>';
  list.innerHTML = html;
}

// ==================== 4. 角色与权限拉取与新建 ====================
async function loadRolesAndPermissions() {
  const token = localStorage.getItem("bravio_token");
  const headers = { "Authorization": `Bearer ${token}` };

  try {
    const [rolesRes, permsRes] = await Promise.all([
      fetch("/api/v1/rbac/roles", { headers }),
      fetch("/api/v1/rbac/permissions", { headers })
    ]);

    if (rolesRes.ok) {
      cachedRoles = await rolesRes.json();
      renderRolesCards(cachedRoles);
      populateRoleCheckboxes(cachedRoles);
    }
    if (permsRes.ok) {
      cachedPermissions = await permsRes.json();
      populatePermCheckboxes(cachedPermissions);
    }
  } catch (err) {
    console.error("加载角色与权限字典失败:", err);
  }
}

function renderRolesCards(roles) {
  const container = document.getElementById("rolesContainer");
  if (!roles || roles.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted);">暂无角色定义</div>';
    return;
  }

  let html = "";
  roles.forEach(r => {
    html += `
      <div style="border:1px solid var(--border-color); border-radius:8px; padding:16px; background:#ffffff; box-shadow:var(--shadow-sm);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <strong style="font-size:15px; color:var(--text-main);">${escapeHtml(r.name)}</strong>
          <span style="font-size:11px; padding:2px 6px; border-radius:4px; background:#e0e7ff; color:#4338ca; font-weight:600;">
            ${escapeHtml(r.data_scope)}
          </span>
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
          代码: <code>${escapeHtml(r.code)}</code><br>
          ${escapeHtml(r.description || "无详细描述")}
        </div>
        <div style="font-size:11.5px; font-weight:600; color:#475569; margin-bottom:6px;">包含功能权限 (${(r.permissions || []).length} 项):</div>
        <div style="max-height:90px; overflow-y:auto; font-size:11px; color:#64748b; line-height:1.6;">
          ${(r.permissions || []).map(p => `• ${escapeHtml(p.name)}`).join("<br>")}
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function populateRoleCheckboxes(roles) {
  const container = document.getElementById("accRolesCheckboxGroup");
  if (!container) return;
  let html = "";
  roles.forEach(r => {
    html += `
      <label style="display:inline-flex; align-items:center; gap:6px; font-size:13px; background:#f1f5f9; padding:4px 10px; border-radius:4px; cursor:pointer;">
        <input type="checkbox" name="assignRole" value="${r.id}" ${r.code === 'ROLE_OPERATOR' ? 'checked' : ''}>
        <span>${escapeHtml(r.name)}</span>
      </label>
    `;
  });
  container.innerHTML = html;
}

function populatePermCheckboxes(perms) {
  const container = document.getElementById("rolePermsCheckboxes");
  if (!container) return;
  let html = "";
  perms.forEach(p => {
    html += `
      <div style="margin-bottom:6px;">
        <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
          <input type="checkbox" name="assignPerm" value="${p.id}">
          <span><strong>${escapeHtml(p.name)}</strong> <code style="color:#64748b;">(${escapeHtml(p.code)})</code></span>
        </label>
      </div>
    `;
  });
  container.innerHTML = html;
}

function populateDeptSelects(depts) {
  const empSelect = document.getElementById("empDeptSelect");
  const parentSelect = document.getElementById("deptParentSelect");

  function flattenDepts(nodes, depth = 0) {
    let list = [];
    nodes.forEach(n => {
      list.push({ id: n.id, name: "— ".repeat(depth) + n.name });
      if (n.children && n.children.length > 0) {
        list = list.concat(flattenDepts(n.children, depth + 1));
      }
    });
    return list;
  }

  const flat = flattenDepts(depts);
  if (empSelect) {
    empSelect.innerHTML = '<option value="">请选择所属部门...</option>' + flat.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join("");
  }
  if (parentSelect) {
    parentSelect.innerHTML = '<option value="">(无上级 - 作为根节点)</option>' + flat.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join("");
  }
}

function populateJobSelect(positions) {
  const select = document.getElementById("empJobSelect");
  if (!select) return;
  select.innerHTML = '<option value="">请选择当前岗位...</option>' + positions.map(p => `<option value="${p.id}">${escapeHtml(p.title)} ${p.is_safety_critical ? '★ (安全工位)' : ''}</option>`).join("");
}

// ==================== 5. 抽屉与模态表单动作 (Paper Sheet Modals) ====================
function openNewEmployeeDrawer() {
  document.getElementById("newEmployeeForm").reset();
  switchEmpTab("basic");
  toggleAccountFields(true);
  document.getElementById("newEmployeeModal").style.display = "flex";
}

function closeNewEmployeeDrawer() {
  document.getElementById("newEmployeeModal").style.display = "none";
}

function switchEmpTab(tab) {
  document.getElementById("tabEmpBasic").classList.toggle("active", tab === "basic");
  document.getElementById("tabEmpAccount").classList.toggle("active", tab === "account");
  document.getElementById("contentEmpBasic").style.display = (tab === "basic") ? "block" : "none";
  document.getElementById("contentEmpAccount").style.display = (tab === "account") ? "block" : "none";
}

function toggleAccountFields(isChecked) {
  document.getElementById("accountFieldsContainer").style.display = isChecked ? "grid" : "none";
}

async function handleCreateEmployee(e) {
  e.preventDefault();
  const token = localStorage.getItem("bravio_token");
  const btn = document.getElementById("btnSubmitEmployee");
  btn.disabled = true;
  btn.textContent = "正在创建并配置账号与权限...";

  const employee_no = document.getElementById("empNo").value.trim();
  const name = document.getElementById("empName").value.trim();
  const email = document.getElementById("empEmail").value.trim();
  const phone = document.getElementById("empPhone").value.trim() || null;
  const department_id = document.getElementById("empDeptSelect").value;
  const job_id = document.getElementById("empJobSelect").value || null;

  const createAccount = document.getElementById("empCreateAccountCheck").checked;
  let accountPayload = null;

  if (createAccount) {
    const username = document.getElementById("accUsername").value.trim();
    const password = document.getElementById("accPassword").value;
    if (!username || !password) {
      alert("请填写开通账号所必需的用户名与初始登录密码！");
      btn.disabled = false;
      btn.textContent = "保存员工并开通权限";
      switchEmpTab("account");
      return;
    }
    const roleCheckboxes = document.querySelectorAll('input[name="assignRole"]:checked');
    const roleIds = Array.from(roleCheckboxes).map(c => c.value);

    accountPayload = {
      username: username,
      password: password,
      role_ids: roleIds,
      is_active: true
    };
  }

  const payload = {
    employee_no: employee_no,
    name: name,
    email: email,
    phone: phone,
    department_id: department_id,
    job_id: job_id,
    status: "ACTIVE",
    account: accountPayload
  };

  try {
    const res = await fetch("/api/v1/org/employees", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "创建员工失败");
    }

    alert(`🎉 成功录入员工档案 [${data.name}]！\n工号: ${data.employee_no}\n${data.account_username ? `系统登录用户名: ${data.account_username}` : '未开通账号'}`);
    closeNewEmployeeDrawer();
    loadOrganizationData();
  } catch (err) {
    alert("录入员工失败: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "保存员工并开通权限";
  }
}

// 新建部门
function openNewDeptModal() {
  document.getElementById("newDeptForm").reset();
  document.getElementById("newDeptModal").style.display = "flex";
}
function closeNewDeptModal() {
  document.getElementById("newDeptModal").style.display = "none";
}
async function handleCreateDepartment(e) {
  e.preventDefault();
  const token = localStorage.getItem("bravio_token");
  const code = document.getElementById("deptCode").value.trim();
  const name = document.getElementById("deptName").value.trim();
  const parent_id = document.getElementById("deptParentSelect").value || null;
  const iso_process_type = document.getElementById("deptIsoType").value;
  const description = document.getElementById("deptDesc").value.trim() || null;

  try {
    const res = await fetch("/api/v1/org/departments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ code, name, parent_id, iso_process_type, description })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "创建部门失败");

    alert(`✅ 成功创建新部门: ${data.name} (${data.code})`);
    closeNewDeptModal();
    loadOrganizationData();
  } catch (err) {
    alert("创建部门失败: " + err.message);
  }
}

// 新建角色
function openNewRoleModal() {
  document.getElementById("newRoleForm").reset();
  document.getElementById("newRoleModal").style.display = "flex";
}
function closeNewRoleModal() {
  document.getElementById("newRoleModal").style.display = "none";
}
async function handleCreateRole(e) {
  e.preventDefault();
  const token = localStorage.getItem("bravio_token");
  const code = document.getElementById("roleCode").value.trim();
  const name = document.getElementById("roleName").value.trim();
  const data_scope = document.getElementById("roleDataScope").value;
  const permCheckboxes = document.querySelectorAll('input[name="assignPerm"]:checked');
  const perm_ids = Array.from(permCheckboxes).map(c => c.value);

  try {
    const res = await fetch("/api/v1/rbac/roles", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ code, name, data_scope, permission_ids: perm_ids })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "创建角色失败");

    alert(`✅ 成功定义系统角色: ${data.name} (${data.code})`);
    closeNewRoleModal();
    loadRolesAndPermissions();
  } catch (err) {
    alert("创建角色失败: " + err.message);
  }
}

// ==================== 6. 开发者实时日志轮询 (限管理员模式) ====================
async function fetchHealth() {
  try {
    const res = await fetch("/api/v1/system/health");
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("statHealthStatus").textContent = data.status.toUpperCase();
    document.getElementById("statDbStatus").textContent = data.database.toUpperCase();
    document.getElementById("statUptime").textContent = `${data.uptime_seconds.toFixed(1)} s`;
    document.getElementById("statVersion").textContent = `v${data.version}`;
  } catch (err) {}
}

async function refreshLogs() {
  try {
    let url = "/api/v1/system/logs?limit=50";
    if (currentLogLevelFilter) {
      url += `&level=${encodeURIComponent(currentLogLevelFilter)}`;
    }
    const res = await fetch(url);
    if (!res.ok) return;
    const logs = await res.json();
    renderLogs(logs);
  } catch (err) {}
}

function renderLogs(logs) {
  const container = document.getElementById("logsContainer");
  if (!container) return;
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="log-line"><span class="log-time">[空]</span><span class="log-msg">暂无符合条件的日志记录</span></div>';
    return;
  }

  let html = "";
  logs.forEach(log => {
    const levelClass = `level-${log.level}`;
    const timeStr = log.timestamp.split("T")[1].replace("Z", "");
    html += `
      <div class="log-line">
        <span class="log-time">[${timeStr}]</span>
        <span class="log-level ${levelClass}">${log.level}</span>
        <span class="log-loc">[${escapeHtml(log.location)}]</span>
        <span class="log-msg">${escapeHtml(log.message)}</span>
      </div>
    `;
  });
  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

function filterLogs(level) {
  currentLogLevelFilter = level;
  ["filterAll", "filterInfo", "filterWarn", "filterError"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.classList.remove("active");
  });
  const map = { null: "filterAll", "INFO": "filterInfo", "WARNING": "filterWarn", "ERROR": "filterError" };
  const targetBtn = document.getElementById(map[level]);
  if (targetBtn) targetBtn.classList.add("active");
  refreshLogs();
}

async function triggerTestLog(level, message) {
  try {
    await fetch(`/api/v1/system/logs/test?level=${encodeURIComponent(level)}&message=${encodeURIComponent(message)}`, { method: "POST" });
    setTimeout(refreshLogs, 150);
  } catch (err) {}
}

function clearLocalLogs() {
  const container = document.getElementById("logsContainer");
  if (container) {
    container.innerHTML = '<div class="log-line"><span class="log-time">[已清屏]</span><span class="log-msg">等待新日志流入...</span></div>';
  }
}

function startPolling() {
  stopPolling();
  logPollTimer = setInterval(refreshLogs, 3000);
  healthPollTimer = setInterval(fetchHealth, 5000);
}

function stopPolling() {
  if (logPollTimer) clearInterval(logPollTimer);
  if (healthPollTimer) clearInterval(healthPollTimer);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[m]));
}
