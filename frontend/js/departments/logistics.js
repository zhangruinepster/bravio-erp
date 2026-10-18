// 📦 仓储物流与逆向售后中心 (WMS & Reverse RMA)
window.DepartmentLogistics = {
  currentSub: "units",

  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">📦 仓储物流与逆向售后中心 (WMS & Reverse RMA)</h2>
          <p class="dept-subtitle">四级包装聚合树 (SN->BOX->CTN->PLT)、德国慕尼黑仓抽检拆解、售后 RMA 换盒欺诈拦截与精准补发 (docs/08 & docs/09)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentLogistics.openNewRmaModal()">+ 登记售后退回件 (RMA)</button>
        </div>
      </div>

      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnLogUnits" onclick="window.DepartmentLogistics.switchSub('units')">🌳 四级包装聚合树台账 (SN->BOX->CTN->PLT)</button>
        <button class="sub-nav-btn" id="btnLogRma" onclick="window.DepartmentLogistics.switchSub('rma')">🛡️ 售后 RMA 逆向风控与反欺诈验真 (Doc 09)</button>
      </div>

      <div id="logSubContent" style="margin-top:16px;"></div>
    `;

    await this.switchSub("units");
  },

  async switchSub(sub) {
    this.currentSub = sub;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const map = { units: 'btnLogUnits', rma: 'btnLogRma' };
    const bEl = document.getElementById(map[sub]);
    if (bEl) bEl.classList.add("active");

    const content = document.getElementById("logSubContent");
    if (sub === "units") await this.renderUnits(content);
    else if (sub === "rma") await this.renderRma(content);
  },

  async renderUnits(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取包装聚合节点...</div>`;
    try {
      const units = await ApiClient.get("/wms/units");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>包装单元编码</th>
                <th>层级 (Level)</th>
                <th>仓库库位</th>
                <th>当前流转状态</th>
                <th>子节点数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${units.map(u => `
                <tr>
                  <td><code>${u.unit_code}</code></td>
                  <td><span class="badge badge-info">${u.level}</span></td>
                  <td>${u.warehouse_location || 'MUC-WH-A-01'}</td>
                  <td>
                    <span class="badge ${u.status === 'PARTIAL_OPENED' ? 'badge-warning' : (u.status === 'LOOSE_SPARE_POOL' ? 'badge-secondary' : 'badge-success')}">
                      ${u.status}
                    </span>
                  </td>
                  <td>${u.children_count} 个下级</td>
                  <td>
                    ${u.level === 'CARTON' && u.status !== 'PARTIAL_OPENED' ? `
                      <button class="btn-secondary" style="padding:4px 8px; font-size:12px;" onclick="window.DepartmentLogistics.triggerDeconstruct('${u.unit_code}')">抽检解包 ➔</button>
                    ` : '<span style="color:var(--text-muted);">--</span>'}
                  </td>
                </tr>
              `).join("") || '<tr><td colspan="6">暂无包装单元</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderRma(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取售后 RMA 风控工单...</div>`;
    try {
      const rmas = await ApiClient.get("/rma");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>RMA 编号</th>
                <th>退货客户</th>
                <th>退回单品序列号 (32位)</th>
                <th>退回外盒码</th>
                <th>报障原因</th>
                <th>防伪欺诈判定</th>
                <th>慕尼黑留样定位</th>
                <th>售后状态</th>
              </tr>
            </thead>
            <tbody>
              ${rmas.map(r => `
                <tr>
                  <td><code>${r.rma_number}</code></td>
                  <td><strong>${r.customer_name}</strong></td>
                  <td><code>${r.returned_sn.substring(0, 18)}...</code></td>
                  <td><code>${r.returned_box_code || '--'}</code></td>
                  <td>${r.claim_reason}</td>
                  <td>
                    ${r.is_fraud_detected ? `
                      <span class="badge badge-danger">⚠️ 拦截: ${r.fraud_reason}</span>
                    ` : '<span class="badge badge-success">✓ 验真合规</span>'}
                  </td>
                  <td>${r.sample_location_matched || 'MUC-LAB-SHELF-04B'}</td>
                  <td><span class="badge ${r.status === 'FRAUD_REJECTED' ? 'badge-danger' : 'badge-info'}">${r.status}</span></td>
                </tr>
              `).join("") || '<tr><td colspan="8">暂无 RMA 记录</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async triggerDeconstruct(cartonCode) {
    const boxCode = prompt("请输入要拆开抽检的彩盒码 (BOX Code):", "BOX-99824-2642-000501");
    if (!boxCode) return;
    try {
      await ApiClient.post("/wms/deconstruct-sample", {
        carton_code: cartonCode,
        box_code_to_remove: boxCode,
        reason: "德国慕尼黑仓 IQC 入库抽检"
      });
      alert(`抽检拆解成功：外箱已降级为 PARTIAL_OPENED，彩盒 [${boxCode}] 已归集入散件备用池！`);
      await this.renderUnits(document.getElementById("logSubContent"));
    } catch (err) {
      alert("操作失败: " + err.message);
    }
  },

  openNewRmaModal() {
    alert("请录入售后退回件的 32 位激光码与彩盒码，系统将自动进行防伪核验与换盒欺诈比对！");
  }
};
