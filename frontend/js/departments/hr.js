// 👥 人力资源与组织中心 (HR & Organization)
window.DepartmentHr = {
  currentTab: "employees",

  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">👥 人力资源与组织合规中心 (HR & Competency)</h2>
          <p class="dept-subtitle">多级组织架构树、员工花名册、KBA/ISO 关键工位资质预警与系统账号权限联动 (docs/04)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentHr.openCreateDrawer()">+ 录入新员工</button>
        </div>
      </div>

      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnHrEmp" onclick="window.DepartmentHr.switchTab('employees')">📋 员工花名册与系统账号</button>
        <button class="sub-nav-btn" id="btnHrDept" onclick="window.DepartmentHr.switchTab('deptTree')">🏢 多级组织架构树</button>
        <button class="sub-nav-btn" id="btnHrCert" onclick="window.DepartmentHr.switchTab('competency')">🛡️ 关键安全工位与资质预警 (KBA)</button>
      </div>

      <div id="hrTabContent" style="margin-top:16px;"></div>
    `;

    await this.switchTab("employees");
  },

  async switchTab(tab) {
    this.currentTab = tab;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById(tab === 'employees' ? 'btnHrEmp' : (tab === 'deptTree' ? 'btnHrDept' : 'btnHrCert'));
    if (activeBtn) activeBtn.classList.add("active");

    const content = document.getElementById("hrTabContent");
    if (tab === "employees") {
      await this.renderEmployees(content);
    } else if (tab === "deptTree") {
      await this.renderDeptTree(content);
    } else if (tab === "competency") {
      await this.renderCompetency(content);
    }
  },

  async renderEmployees(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取员工花名册...</div>`;
    try {
      const emps = await ApiClient.get("/org/employees");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>工号</th>
                <th>姓名</th>
                <th>所属部门</th>
                <th>岗位职责</th>
                <th>系统绑定账号</th>
                <th>角色与权限</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${emps.map(e => `
                <tr>
                  <td><code>${e.employee_no}</code></td>
                  <td>
                    <div style="display:flex; align-items:center; gap:8px;">
                      <img src="${e.avatar_url || 'assets/demo_images/avatar_default.svg'}" style="width:32px; height:32px; border-radius:50%; object-fit:cover; border:1.5px solid var(--border-color); flex-shrink:0; background:#fff;">
                      <a class="table-action-link" href="javascript:void(0)" onclick="window.DepartmentHr.openEmployeeDetail('${e.id}')">
                        <strong>${e.name}</strong>
                      </a>
                    </div>
                  </td>
                  <td>${e.department_name || '未分配'}</td>
                  <td>${e.job_title || '未设定'}</td>
                  <td>${e.account_username ? `<span class="badge badge-info">🔐 ${e.account_username}</span>` : '<span style="color:var(--text-muted);">未开通</span>'}</td>
                  <td>${e.account_roles && e.account_roles.length ? e.account_roles.map(r => `<span class="badge badge-secondary">${r}</span>`).join(' ') : '--'}</td>
                  <td><span class="badge badge-success">${e.status}</span></td>
                  <td>
                    <button class="btn-secondary btn-xs" onclick="window.DepartmentHr.openEmployeeDetail('${e.id}')">查看/编辑</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderDeptTree(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取部门树...</div>`;
    try {
      const depts = await ApiClient.get("/org/departments");
      container.innerHTML = `
        <div class="content-card">
          <h3 style="margin-bottom:12px;">🏢 集团多级组织架构树 (ISO 9001 过程分类)</h3>
          <div style="display:flex; flex-direction:column; gap:10px;">
            ${depts.map(d => `
              <div style="padding:12px 16px; border:1px solid var(--border-color); border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <strong>${d.name}</strong> <code>[${d.code}]</code>
                  <div style="font-size:12px; color:var(--text-muted); margin-top:3px;">${d.description || '无描述'}</div>
                </div>
                <span class="badge badge-info">${d.iso_process_type}</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderCompetency(container) {
    container.innerHTML = `<div class="loading-spinner">正在审查 KBA/ISO 关键工位资质...</div>`;
    try {
      const [warningCerts, emps] = await Promise.all([
        ApiClient.get("/org/certifications/expiring?days=30"),
        ApiClient.get("/org/employees")
      ]);

      container.innerHTML = `
        <div class="content-card" style="margin-bottom:16px; border-left:4px solid var(--warning);">
          <div style="font-weight:700; color:var(--warning); margin-bottom:8px;">⚠️ 30 天内临期预警资质证书 (${warningCerts.length} 项)</div>
          ${warningCerts.map(c => `
            <div style="padding:8px 0; border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between;">
              <span><strong>${c.cert_name}</strong> (${c.cert_no}) · 到期日: ${c.expiry_date.substring(0, 10)}</span>
              <span class="badge badge-warning">剩余 ${c.days_to_expire} 天</span>
            </div>
          `).join("") || "暂无30天内临期预警证书"}
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async openCreateDrawer() {
    const existing = document.getElementById("hrEmpModalOverlay");
    if (existing) existing.remove();

    try {
      const [depts, positions, roles] = await Promise.all([
        ApiClient.get("/org/departments"),
        ApiClient.get("/org/positions"),
        ApiClient.get("/rbac/roles").catch(() => [])
      ]);

      const overlay = document.createElement("div");
      overlay.id = "hrEmpModalOverlay";
      overlay.className = "erp-modal-overlay";
      overlay.innerHTML = `
        <div class="erp-modal-container large" onclick="event.stopPropagation()">
          <div class="erp-modal-header">
            <h3>👥 录入新员工入职档案 (ISO 9001 人力资源中枢)</h3>
            <button class="erp-modal-close-btn" onclick="document.getElementById('hrEmpModalOverlay').remove()">✕</button>
          </div>
          <div class="erp-modal-body">
            <form id="newEmpForm" onsubmit="event.preventDefault(); window.DepartmentHr.submitNewEmployee();">
              <div class="form-grid-2">
                <div class="form-group">
                  <label class="form-label">工号 (Employee No) *</label>
                  <input type="text" id="neNo" class="form-input" placeholder="如 BR-2026-302" required>
                </div>
                <div class="form-group">
                  <label class="form-label">员工真实姓名 *</label>
                  <input type="text" id="neName" class="form-input" placeholder="如 赵工匠" required>
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">工作电子邮箱 *</label>
                  <input type="email" id="neEmail" class="form-input" placeholder="如 zhao@bravio-erp.com" required>
                </div>
                <div class="form-group">
                  <label class="form-label">联系电话</label>
                  <input type="text" id="nePhone" class="form-input" placeholder="如 +49 89 55667788">
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">所属部门 (Department) *</label>
                  <select id="neDept" class="form-select" required>
                    <option value="">-- 请选择所属部门 --</option>
                    ${depts.map(d => `<option value="${d.id}">${d.name} [${d.code}]</option>`).join("")}
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">岗位职责 (Job Position)</label>
                  <select id="neJob" class="form-select">
                    <option value="">-- 请选择岗位 --</option>
                    ${positions.map(p => `<option value="${p.id}">${p.title} ${p.is_safety_critical ? '⚠️(安全工位)' : ''}</option>`).join("")}
                  </select>
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">在职状态</label>
                  <select id="neStatus" class="form-select">
                    <option value="ACTIVE" selected>ACTIVE (在职)</option>
                    <option value="PROBATION">PROBATION (试用期)</option>
                    <option value="SUSPENDED">SUSPENDED (挂职)</option>
                    <option value="TERMINATED">TERMINATED (离职)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">入职生效日期</label>
                  <input type="date" id="neHireDate" class="form-input" value="${new Date().toISOString().substring(0, 10)}">
                </div>
              </div>

              <!-- 可选同时开通系统账号 -->
              <div style="margin-top:16px; padding:14px; background:#f8fafc; border:1px dashed var(--border-color); border-radius:8px;">
                <label style="font-weight:700; font-size:13px; color:var(--text-main); display:flex; align-items:center; gap:8px; cursor:pointer;">
                  <input type="checkbox" id="neCreateAccount" onchange="document.getElementById('accFieldsBox').style.display = this.checked ? 'block' : 'none';">
                  <span>🔐 一键同步开通 Bravio ERP 系统登录账号与岗位权限</span>
                </label>

                <div id="accFieldsBox" style="display:none; margin-top:12px;">
                  <div class="form-grid-2">
                    <div class="form-group">
                      <label class="form-label">登录用户名 (Username) *</label>
                      <input type="text" id="neAccUser" class="form-input" placeholder="输入账号，如 zhao">
                    </div>
                    <div class="form-group">
                      <label class="form-label">初始会话密码 (Password) *</label>
                      <input type="password" id="neAccPass" class="form-input" placeholder="至少 6 位，如 123456" value="123456">
                    </div>
                  </div>

                  <div class="form-group" style="margin-top:10px;">
                    <label class="form-label">分配系统初始角色 (RBAC)</label>
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:4px;">
                      ${roles.map(r => `
                        <label style="font-size:12px; display:inline-flex; align-items:center; gap:4px; padding:4px 8px; background:#fff; border:1px solid var(--border-color); border-radius:4px; cursor:pointer;">
                          <input type="checkbox" name="neRoleCb" value="${r.id}">
                          <span>${r.name}</span>
                        </label>
                      `).join("") || '<span style="color:var(--text-muted); font-size:12px;">暂无可选角色</span>'}
                    </div>
                  </div>
                </div>
              </div>

              <div style="margin-top:18px; display:flex; justify-content:flex-end; gap:10px;">
                <button type="button" class="btn-secondary" onclick="document.getElementById('hrEmpModalOverlay').remove()">取消</button>
                <button type="submit" id="neSubmitBtn" class="btn-primary">✓ 录入新员工档案</button>
              </div>
            </form>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    } catch (err) {
      alert("加载基础数据失败: " + err.message);
    }
  },

  async submitNewEmployee() {
    const btn = document.getElementById("neSubmitBtn");
    btn.disabled = true;
    btn.textContent = "正在提交录入...";

    const isCreateAcc = document.getElementById("neCreateAccount").checked;
    let accountObj = null;

    if (isCreateAcc) {
      const u = document.getElementById("neAccUser").value.trim();
      const p = document.getElementById("neAccPass").value;
      if (!u || !p) {
        alert("请完整填写系统账号用户名与密码！");
        btn.disabled = false;
        btn.textContent = "✓ 录入新员工档案";
        return;
      }
      const roleIds = Array.from(document.querySelectorAll("input[name='neRoleCb']:checked")).map(cb => cb.value);
      accountObj = {
        username: u,
        password: p,
        role_ids: roleIds,
        is_active: true
      };
    }

    const payload = {
      employee_no: document.getElementById("neNo").value.trim(),
      name: document.getElementById("neName").value.trim(),
      email: document.getElementById("neEmail").value.trim(),
      phone: document.getElementById("nePhone").value.trim() || null,
      department_id: document.getElementById("neDept").value,
      job_id: document.getElementById("neJob").value || null,
      status: document.getElementById("neStatus").value,
      hire_date: new Date(document.getElementById("neHireDate").value).toISOString(),
      account: accountObj
    };

    try {
      const res = await ApiClient.post("/org/employees", payload);
      alert(`🎉 新员工录入成功！\n工号: ${res.employee_no}\n姓名: ${res.name}\n${res.account_username ? '已自动开通系统账号: ' + res.account_username : '未绑定系统账号'}`);
      const m = document.getElementById("hrEmpModalOverlay");
      if (m) m.remove();
      await this.renderEmployees(document.getElementById("hrTabContent"));
    } catch (err) {
      alert("录入失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✓ 录入新员工档案";
      }
    }
  },

  async openEmployeeDetail(empId) {
    const existing = document.getElementById("hrEmpDetailModalOverlay");
    if (existing) existing.remove();

    try {
      const [e, depts, positions] = await Promise.all([
        ApiClient.get(`/org/employees/${empId}`),
        ApiClient.get("/org/departments"),
        ApiClient.get("/org/positions")
      ]);

      const overlay = document.createElement("div");
      overlay.id = "hrEmpDetailModalOverlay";
      overlay.className = "erp-modal-overlay";
      overlay.innerHTML = `
        <div class="erp-modal-container large" onclick="event.stopPropagation()">
          <div class="erp-modal-header">
            <div>
              <h3>👥 员工人事档案详情与合规资质审查</h3>
              <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                工号: <code>${e.employee_no}</code> · 入职时间: ${e.hire_date ? e.hire_date.substring(0, 10) : '未登记'}
              </p>
            </div>
            <button class="erp-modal-close-btn" onclick="document.getElementById('hrEmpDetailModalOverlay').remove()">✕</button>
          </div>
          <div class="erp-modal-body">
            <!-- 头部基本属性与右上角头像区域 (按需求 1：排版在 UI 卡片显示的右上方位置) -->
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:20px; background:#f8fafc; border:1px solid var(--border-color); border-radius:10px; padding:16px; margin-bottom:16px;">
              <!-- 左侧：员工档案基本摘要 -->
              <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                  <h2 style="font-size:20px; font-weight:800; color:var(--text-main); margin:0;">${e.name}</h2>
                  <span class="badge badge-success">${e.status}</span>
                  ${e.competency_status && e.competency_status.is_safety_critical_job ? '<span class="badge badge-danger">SC/CC 安全关键岗位</span>' : ''}
                </div>
                <div style="font-size:13px; color:var(--text-muted); line-height:1.6;">
                  <div>所属部门: <strong>${e.department_name || '未分配'}</strong> · 岗位: <strong>${e.job_title || '未设定'}</strong></div>
                  <div>工作邮箱: <a href="mailto:${e.email}">${e.email}</a> · 联系电话: ${e.phone || '未登记'}</div>
                  <div style="margin-top:4px;">
                    系统账号: ${e.account_username ? `<strong>🔐 ${e.account_username}</strong>` : '<span style="color:var(--text-muted);">未开通</span>'}
                    ${e.account_roles && e.account_roles.length ? e.account_roles.map(r => `<span class="badge badge-secondary" style="margin-left:4px;">${r}</span>`).join('') : ''}
                  </div>
                </div>
              </div>

              <!-- 右上方：员工电子头像档案卡片 (排版在卡片右上方) -->
              <div style="width:140px; flex-shrink:0; display:flex; flex-direction:column; align-items:center; text-align:center; padding:10px; background:#ffffff; border:1px solid var(--border-color); border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="position:relative; width:80px; height:80px; margin-bottom:8px;">
                  <img id="eeAvatarImg" src="${e.avatar_url || 'assets/demo_images/avatar_default.svg'}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border:2.5px solid #3b82f6; background:#f1f5f9; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
                </div>
                <div style="font-size:11px; font-weight:700; color:var(--text-muted); margin-bottom:6px;">档案照片 / 头像</div>
                <div style="display:flex; flex-direction:column; gap:4px; width:100%;">
                  <button type="button" class="btn-secondary btn-xs" style="width:100%; font-size:11px; padding:3px 6px;" onclick="document.getElementById('eeAvatarFileInput').click()">📸 上传头像</button>
                  <input type="file" id="eeAvatarFileInput" accept="image/*" style="display:none;" onchange="window.DepartmentHr.handleAvatarUpload('${e.id}', this)">
                  <button type="button" class="btn-secondary btn-xs" style="width:100%; font-size:11px; padding:3px 6px;" onclick="window.DepartmentHr.openDemoAvatarPicker('${e.id}')">✨ 选预置Demo</button>
                </div>
              </div>
            </div>

            <!-- 持有证书清单 -->
            ${e.certifications && e.certifications.length ? `
              <div style="margin-bottom:16px;">
                <div style="font-size:12.5px; font-weight:700; color:var(--text-main); margin-bottom:6px;">🛡️ 已登记 ISO / KBA 资质证书 (${e.certifications.length} 本)</div>
                <div style="display:flex; flex-direction:column; gap:6px;">
                  ${e.certifications.map(c => `
                    <div style="padding:8px 12px; background:#ffffff; border:1px solid var(--border-color); border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
                      <div>
                        <strong>${c.cert_name}</strong> <code>[${c.cert_no}]</code>
                        <span style="font-size:11.5px; color:var(--text-muted); margin-left:8px;">颁发机构: ${c.issuing_authority}</span>
                      </div>
                      <div>
                        ${c.is_expired ? '<span class="badge badge-danger">已过期</span>' : (c.is_warning ? `<span class="badge badge-warning">临期预警: 剩余 ${c.days_to_expire} 天</span>` : '<span class="badge badge-success">正常有效</span>')}
                      </div>
                    </div>
                  `).join("")}
                </div>
              </div>
            ` : ''}

            <!-- 编辑人事基础属性表单 -->
            <form id="editEmpForm" onsubmit="event.preventDefault(); window.DepartmentHr.saveEmployeeChanges('${e.id}');">
              <div class="form-grid-2">
                <div class="form-group">
                  <label class="form-label">员工真实姓名 *</label>
                  <input type="text" id="eeName" class="form-input" value="${e.name || ''}" required>
                </div>
                <div class="form-group">
                  <label class="form-label">工作电子邮箱 *</label>
                  <input type="email" id="eeEmail" class="form-input" value="${e.email || ''}" required>
                </div>
              </div>

              <div class="form-grid-3" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">联系电话</label>
                  <input type="text" id="eePhone" class="form-input" value="${e.phone || ''}">
                </div>
                <div class="form-group">
                  <label class="form-label">所属部门 *</label>
                  <select id="eeDept" class="form-select" required>
                    ${depts.map(d => `<option value="${d.id}" ${d.id === e.department_id ? 'selected' : ''}>${d.name}</option>`).join("")}
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">岗位职责</label>
                  <select id="eeJob" class="form-select">
                    <option value="">-- 未设置岗位 --</option>
                    ${positions.map(p => `<option value="${p.id}" ${p.id === e.job_id ? 'selected' : ''}>${p.title}</option>`).join("")}
                  </select>
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">在职状态</label>
                  <select id="eeStatus" class="form-select">
                    <option value="ACTIVE" ${e.status === 'ACTIVE' ? 'selected' : ''}>ACTIVE (在职)</option>
                    <option value="PROBATION" ${e.status === 'PROBATION' ? 'selected' : ''}>PROBATION (试用期)</option>
                    <option value="SUSPENDED" ${e.status === 'SUSPENDED' ? 'selected' : ''}>SUSPENDED (挂职)</option>
                    <option value="TERMINATED" ${e.status === 'TERMINATED' ? 'selected' : ''}>TERMINATED (离职)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">最后档案更新</label>
                  <input type="text" class="form-input" value="${e.created_at ? e.created_at.substring(0, 19).replace('T', ' ') : '--'}" readonly style="background:#f1f5f9;">
                </div>
              </div>

              <div style="margin-top:18px; display:flex; justify-content:flex-end; gap:10px;">
                <button type="button" class="btn-secondary" onclick="document.getElementById('hrEmpDetailModalOverlay').remove()">取消</button>
                <button type="submit" id="eeSaveBtn" class="btn-primary">💾 保存人事修改并重新审核资质</button>
              </div>
            </form>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    } catch (err) {
      alert("加载员工详情失败: " + err.message);
    }
  },

  async saveEmployeeChanges(empId) {
    const btn = document.getElementById("eeSaveBtn");
    btn.disabled = true;
    btn.textContent = "正在保存变更...";

    const payload = {
      name: document.getElementById("eeName").value.trim(),
      email: document.getElementById("eeEmail").value.trim(),
      phone: document.getElementById("eePhone").value.trim() || null,
      department_id: document.getElementById("eeDept").value,
      job_id: document.getElementById("eeJob").value || null,
      status: document.getElementById("eeStatus").value
    };

    try {
      await ApiClient.put(`/org/employees/${empId}`, payload);
      alert("✓ 员工档案信息更新成功！");
      const m = document.getElementById("hrEmpDetailModalOverlay");
      if (m) m.remove();
      await this.renderEmployees(document.getElementById("hrTabContent"));
    } catch (err) {
      alert("保存失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "💾 保存人事修改并重新审核资质";
      }
    }
  },

  async handleAvatarUpload(empId, fileInput) {
    if (!fileInput.files || !fileInput.files[0]) return;
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("res_model", "hr_employee");
    formData.append("res_id", empId);
    formData.append("description", `员工头像上传`);

    try {
      const res = await ApiClient.uploadFormData("/system/attachments/upload", formData);
      const img = document.getElementById("eeAvatarImg");
      if (img) img.src = res.file_url + "?t=" + Date.now();
      alert("✓ 员工头像上传并更新成功！");
      await this.renderEmployees(document.getElementById("hrTabContent"));
    } catch (err) {
      alert("上传头像失败: " + err.message);
    }
  },

  openDemoAvatarPicker(empId) {
    const demos = [
      { file: "avatar_dr_zhang.svg", title: "张合规博士 (合规/审核)" },
      { file: "avatar_chen_gm.svg", title: "陈总裁 (高管/西装)" },
      { file: "avatar_wang_pe.svg", title: "王工程 (研发/技术)" },
      { file: "avatar_liu_qe.svg", title: "刘质保 (质量/工程师)" },
      { file: "avatar_li_quality.svg", title: "李质保 (部门负责人)" },
      { file: "avatar_default.svg", title: "标准通用企业头像" }
    ];

    const pickerOverlay = document.createElement("div");
    pickerOverlay.id = "demoAvatarPickerOverlay";
    pickerOverlay.className = "erp-modal-overlay";
    pickerOverlay.style.zIndex = "1050";
    pickerOverlay.innerHTML = `
      <div class="erp-modal-container small" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>✨ 选择员工预置 Demo 头像素材</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('demoAvatarPickerOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-top:8px;">
            ${demos.map(d => `
              <div onclick="window.DepartmentHr.selectDemoAvatar('${empId}', '${d.file}')" style="cursor:pointer; border:1px solid var(--border-color); border-radius:8px; padding:10px; text-align:center; transition:all 0.2s;" onmouseover="this.style.borderColor='#3b82f6'; this.style.background='#f0f9ff';" onmouseout="this.style.borderColor='var(--border-color)'; this.style.background='#fff';">
                <img src="assets/demo_images/${d.file}" style="width:56px; height:56px; border-radius:50%; margin-bottom:6px; border:2px solid #e2e8f0; object-fit:cover;">
                <div style="font-size:11px; font-weight:700; color:var(--text-main);">${d.title}</div>
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(pickerOverlay);
  },

  async selectDemoAvatar(empId, demoFile) {
    try {
      const res = await ApiClient.post("/system/attachments/bind-demo", {
        res_model: "hr_employee",
        res_id: empId,
        demo_filename: demoFile,
        description: `选用预置Demo头像: ${demoFile}`
      });
      const img = document.getElementById("eeAvatarImg");
      if (img) img.src = res.file_url + "?t=" + Date.now();
      const p = document.getElementById("demoAvatarPickerOverlay");
      if (p) p.remove();
      alert("✓ 已成功切换为预置 Demo 头像！");
      await this.renderEmployees(document.getElementById("hrTabContent"));
    } catch (err) {
      alert("绑定预置头像失败: " + err.message);
    }
  }
};
