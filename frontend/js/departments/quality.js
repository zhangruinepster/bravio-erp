// 🛡️ 质量保证与合规中心 (Quality & Compliance) - 质量工程师 (QE / 刘质保) 核心工作台
window.DepartmentQuality = {
  currentSub: "inspections",

  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">🛡️ 质量保证与法规合规中心 (Quality & Compliance)</h2>
          <p class="dept-subtitle">质量工程师工作台：进出厂首件质检 (IQC/FQC)、8D 客诉攻关与 CAPA 闭环、德国 KBA 生产一致性 (CoP) 与受控文档库 (docs/14 & docs/15)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentQuality.openNewInspectionModal()">+ 录入首件与出厂检验单</button>
        </div>
      </div>

      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnQaInsp" onclick="window.DepartmentQuality.switchSub('inspections')">📋 全流程质检台账 (IQC / FQC - Doc 14)</button>
        <button class="sub-nav-btn" id="btnQaEightD" onclick="window.DepartmentQuality.switchSub('eightD')">⚡ 8D 质量失效攻关与 CAPA 闭环 (Doc 14)</button>
        <button class="sub-nav-btn" id="btnQaDms" onclick="window.DepartmentQuality.switchSub('dms')">📚 受控体系文档库 (ISO 9001 四层成文信息 - Doc 15)</button>
      </div>

      <div id="qaSubContent" style="margin-top:16px;"></div>
    `;

    await this.switchSub("inspections");
  },

  async switchSub(sub) {
    this.currentSub = sub;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const map = { inspections: 'btnQaInsp', eightD: 'btnQaEightD', dms: 'btnQaDms' };
    const bEl = document.getElementById(map[sub]);
    if (bEl) bEl.classList.add("active");

    const content = document.getElementById("qaSubContent");
    if (sub === "inspections") await this.renderInspections(content);
    else if (sub === "eightD") await this.renderEightD(content);
    else if (sub === "dms") await this.renderDms(content);
  },

  async renderInspections(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取全流程质检单据...</div>`;
    try {
      const insps = await ApiClient.get("/qms/inspections");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>检验单号</th>
                <th>类型</th>
                <th>零件号与生产批次</th>
                <th>抽样 / 不良</th>
                <th>特殊特性尺寸检验</th>
                <th>光学特性与KBA合规</th>
                <th>质检结论</th>
                <th>检验工程师</th>
              </tr>
            </thead>
            <tbody>
              ${insps.map(i => `
                <tr>
                  <td><code>${i.sheet_number}</code></td>
                  <td><span class="badge badge-info">${i.inspection_type}</span></td>
                  <td><strong>${i.bravio_id}</strong> (批次: ${i.batch_number})</td>
                  <td>${i.sample_size} 件 / ${i.defect_count} 不良</td>
                  <td>${i.dimension_check_passed ? '<span class="badge badge-success">✓ 尺寸公差受控</span>' : '<span class="badge badge-danger">超差</span>'}</td>
                  <td>${i.kba_cop_compliant ? '<span class="badge badge-success">✓ KBA CoP 合规</span>' : '<span class="badge badge-danger">不符合</span>'}</td>
                  <td><span class="badge ${i.overall_result === 'PASS' ? 'badge-success' : 'badge-danger'}">${i.overall_result}</span></td>
                  <td>${i.inspector_name}</td>
                </tr>
              `).join("") || '<tr><td colspan="8">暂无质检记录</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderEightD(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取 8D 攻关档案...</div>`;
    try {
      const eightDs = await ApiClient.get("/qms/incidents-8d");
      container.innerHTML = `
        <div style="margin-bottom:12px; display:flex; justify-content:flex-end;">
          <button class="btn-primary" onclick="window.DepartmentQuality.openNewEightDModal()">+ 发起 8D 质量攻关 (客诉/失效)</button>
        </div>
        <div style="display:flex; flex-direction:column; gap:12px;">
          ${eightDs.map(ed => `
            <div class="content-card" style="border-left:4px solid ${ed.status === 'CLOSED' ? 'var(--success)' : 'var(--warning)'};">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <h3>${ed.incident_number} · ${ed.title}</h3>
                  <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
                    负责人: ${ed.d1_team_leader || '未指派'} · 来源: ${ed.source} · 建立时间: ${ed.created_at.substring(0, 10)}
                  </div>
                </div>
                <span class="badge ${ed.status === 'CLOSED' ? 'badge-success' : 'badge-warning'}">${ed.status}</span>
              </div>
              <div style="margin-top:12px; font-size:13.5px; line-height:1.6; background:#f8fafc; padding:12px; border-radius:6px;">
                <div><strong>D2 现象描述：</strong>${ed.d2_problem_description}</div>
                ${ed.d3_interim_containment ? `<div><strong>D3 围堵措施：</strong>${ed.d3_interim_containment}</div>` : ''}
                ${ed.d4_root_cause ? `<div><strong>D4 根本原因 (5-Why)：</strong>${ed.d4_root_cause}</div>` : ''}
              </div>
            </div>
          `).join("") || '<div class="content-card">暂无 8D 客诉工单</div>'}
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderDms(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取受控体系文档金字塔...</div>`;
    try {
      const docs = await ApiClient.get("/dms/documents");
      container.innerHTML = `
        <div class="content-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <h3>📚 ISO 9001 四层金字塔受控成文信息 (docs/15)</h3>
            <span class="badge badge-success">动态防泄密水印保护中</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>受控文档编号</th>
                  <th>体系文件标题</th>
                  <th>金字塔层级</th>
                  <th>生效版本</th>
                  <th>受控范围</th>
                  <th>状态</th>
                  <th>水印标记</th>
                </tr>
              </thead>
              <tbody>
                ${docs.map(d => `
                  <tr>
                    <td><code>${d.doc_number}</code></td>
                    <td><strong>${d.title}</strong><div style="font-size:12px; color:var(--text-muted);">${d.summary || ''}</div></td>
                    <td><span class="badge badge-info">${d.doc_level}</span></td>
                    <td><span class="badge badge-secondary">${d.version}</span></td>
                    <td>${d.department_scope}</td>
                    <td><span class="badge badge-success">${d.status}</span></td>
                    <td><small style="color:var(--text-muted);">${d.watermark_text}</small></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  openNewInspectionModal() {
    alert("请录入批次抽检数据，系统将自动核算尺寸公差与 KBA CoP 达标情况！");
  },

  openNewEightDModal() {
    alert("正在启动质量 8D 攻关组！");
  }
};
