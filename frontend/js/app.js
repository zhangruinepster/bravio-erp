// Bravio ERP V0.3.1 前端主控制器 (按部门和角色分类 - docs/02)
const DEPARTMENTS = [
  { id: "executive", name: "🏢 总裁办与执行委员会", roleHint: "集团总经理 (gm)", desc: "企业全盘经营驾驶舱、重大质量审批", module: window.DepartmentExecutive },
  { id: "hr", name: "👥 人力资源与组织中心", roleHint: "HR / 审核专员", desc: "组织架构树、员工花名册、KBA资质预警", module: window.DepartmentHr },
  { id: "engineering", name: "📐 研发与工程技术中心", roleHint: "产品工程师 (pe)", desc: "产品主数据、APQP阶段门、BOM、ECM工程变更", module: window.DepartmentEngineering },
  { id: "quality", name: "🛡️ 质量保证与合规中心", roleHint: "质量工程师 (qe)", desc: "进出厂首件检验、8D客诉、KBA一致性、受控DMS", module: window.DepartmentQuality },
  { id: "manufacturing", name: "🏭 制造与供应链协同中心", roleHint: "供应商专员 (supplier)", desc: "商业伙伴、B2B代工工单、双灯防呆工位", module: window.DepartmentManufacturing },
  { id: "logistics", name: "📦 仓储物流与逆向售后中心", roleHint: "仓管 / 售后工程师", desc: "四级包装树(SN->PLT)、德国仓抽检、RMA欺诈拦截", module: window.DepartmentLogistics },
  { id: "system", name: "🛠️ 数字化与运维中心", roleHint: "仅限系统管理员 (admin)", desc: "数据库实时全景探针、单表检视、一致性快照与实时日志", module: window.DepartmentSystem }
];

class AppManager {
  static currentDeptId = "executive";

  static async init() {
    // 检查会话
    const user = await AuthService.verifySession();
    if (!user) {
      document.getElementById("loginView").style.display = "flex";
      document.getElementById("mainAppView").style.display = "none";
      return;
    }

    // 已经登录
    document.getElementById("loginView").style.display = "none";
    document.getElementById("mainAppView").style.display = "block";

    // 渲染用户信息
    document.getElementById("topUserName").textContent = user.full_name || user.username;
    document.getElementById("topUserRole").textContent = AuthService.getRoleBadge(user);
    document.getElementById("topUserAvatar").textContent = (user.full_name || user.username)[0].toUpperCase();

    // 默认根据角色进入适合的部门中心
    if (user.username === "pe") {
      AppManager.switchDepartment("engineering");
    } else if (user.username === "qe") {
      AppManager.switchDepartment("quality");
    } else if (user.username === "supplier") {
      AppManager.switchDepartment("manufacturing");
    } else if (user.username === "admin") {
      AppManager.switchDepartment("system");
    } else {
      AppManager.switchDepartment("executive");
    }

    AppManager.renderAppSwitcherGrid();
  }

  static renderAppSwitcherGrid() {
    const grid = document.getElementById("deptGridModal");
    if (!grid) return;
    const user = AuthService.getCurrentUser();
    const isAdmin = AuthService.isSuperAdmin(user);

    grid.innerHTML = DEPARTMENTS.map(d => {
      // 非系统管理员隐藏底层运维控制台
      if (d.id === "system" && !isAdmin) return "";
      return `
        <div class="dept-tile ${d.id === AppManager.currentDeptId ? 'active' : ''}" onclick="AppManager.onSelectDeptFromModal('${d.id}')">
          <div class="dept-tile-icon">${d.name.split(' ')[0]}</div>
          <div class="dept-tile-title">${d.name.split(' ')[1]}</div>
          <div class="dept-tile-desc">${d.desc}</div>
          <div style="margin-top:8px;"><span class="badge badge-secondary">${d.roleHint}</span></div>
        </div>
      `;
    }).join("");
  }

  static onSelectDeptFromModal(deptId) {
    AppManager.closeAppSwitcher();
    AppManager.switchDepartment(deptId);
  }

  static async switchDepartment(deptId) {
    const user = AuthService.getCurrentUser();
    // 权限守卫：非管理员禁止进入运维中心
    if (deptId === "system" && !AuthService.isSuperAdmin(user)) {
      alert("【安全阻断】当前角色无权访问底层系统运维控制台！已为您安全切回业务工作台。");
      AppManager.switchDepartment("executive");
      return;
    }

    AppManager.currentDeptId = deptId;
    const dept = DEPARTMENTS.find(d => d.id === deptId) || DEPARTMENTS[0];

    // 更新面包屑
    document.getElementById("breadcrumbDept").textContent = dept.name;

    // 渲染部门工作台
    const container = document.getElementById("departmentWorkspace");
    container.innerHTML = `<div class="loading-spinner">正在装载 ${dept.name} 工作台...</div>`;
    if (dept.module && dept.module.render) {
      await dept.module.render(container);
    }
  }

  static toggleAppSwitcher() {
    const m = document.getElementById("appSwitcherModal");
    m.style.display = (m.style.display === "none" || !m.style.display) ? "flex" : "none";
    AppManager.renderAppSwitcherGrid();
  }

  static closeAppSwitcher() {
    const m = document.getElementById("appSwitcherModal");
    if (m) m.style.display = "none";
  }

  static toggleRoleDropdown(e) {
    if (e) e.stopPropagation();
    const m = document.getElementById("roleDropdownMenu");
    m.style.display = (m.style.display === "none" || !m.style.display) ? "block" : "none";
  }

  static async quickSwitchRole(username, password) {
    document.getElementById("roleDropdownMenu").style.display = "none";
    try {
      await AuthService.login(username, password);
      await AppManager.init();
      // 提示
      alert(`⚡ 已无缝切换到测试身份: ${username}`);
    } catch (err) {
      alert("切换失败: " + err.message);
    }
  }
}

// 全局事件监听
document.addEventListener("click", () => {
  const m = document.getElementById("roleDropdownMenu");
  if (m) m.style.display = "none";
});

window.AppManager = AppManager;

// 页面加载就绪
document.addEventListener("DOMContentLoaded", () => {
  AppManager.init();
});
