// 🏢 总裁办与执行委员会工作台 (Executive Suite / GM)
window.DepartmentExecutive = {
  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">🏢 总裁办与执行委员会 (Executive Suite)</h2>
          <p class="dept-subtitle">统辖集团全盘企业经营、跨部门协同总览与重大质量合规决策 (遵循最小权限：无权访问底层系统日志)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentExecutive.refreshData()">🔄 刷新全盘指标</button>
        </div>
      </div>

      <!-- 企业核心驾驶舱 KPI -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">旗舰车规产品 (APQP)</div>
          <div class="kpi-value" id="kpiProductCount">--</div>
          <div class="kpi-desc">PPAP 试产阶段门推进正常</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">在职人员与组织</div>
          <div class="kpi-value" id="kpiEmployeeCount">--</div>
          <div class="kpi-desc">多级组织架构树覆盖受控</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">出厂质检合格率 (FQC)</div>
          <div class="kpi-value" style="color:var(--success);">100%</div>
          <div class="kpi-desc">德国 KBA 生产一致性达标</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">售后 RMA 风险拦截</div>
          <div class="kpi-value" id="kpiRmaCount" style="color:var(--danger);">--</div>
          <div class="kpi-desc">换盒欺诈拦截风控生效中</div>
        </div>
      </div>

      <!-- 总裁办跨部门总览列表 -->
      <div class="grid-2-col" style="margin-top:20px;">
        <div class="content-card">
          <div class="card-header-bar">
            <h3>📐 研发中心：核心产品主数据与 APQP 阶段门</h3>
            <span class="badge badge-info">Doc 10</span>
          </div>
          <div id="execProductList" class="compact-list">正在汇总数据...</div>
        </div>

        <div class="content-card">
          <div class="card-header-bar">
            <h3>🛡️ 质量中心：8D 异常攻关与 CAPA 闭环</h3>
            <span class="badge badge-warning">Doc 14</span>
          </div>
          <div id="execEightDList" class="compact-list">正在汇总数据...</div>
        </div>
      </div>

      <div class="grid-2-col" style="margin-top:20px;">
        <div class="content-card">
          <div class="card-header-bar">
            <h3>🏭 制造与供应链：商业伙伴与代工工单</h3>
            <span class="badge badge-success">Doc 16/17</span>
          </div>
          <div id="execPartnerList" class="compact-list">正在汇总数据...</div>
        </div>

        <div class="content-card">
          <div class="card-header-bar">
            <h3>📦 逆向风控：最新售后 RMA 审计</h3>
            <span class="badge badge-danger">Doc 09</span>
          </div>
          <div id="execRmaList" class="compact-list">正在汇总数据...</div>
        </div>
      </div>
    `;

    await this.refreshData();
  },

  async refreshData() {
    try {
      const [prods, emps, rmas, eightDs, partners] = await Promise.all([
        ApiClient.get("/products"),
        ApiClient.get("/org/employees"),
        ApiClient.get("/rma"),
        ApiClient.get("/qms/incidents-8d"),
        ApiClient.get("/partners")
      ]);

      document.getElementById("kpiProductCount").textContent = `${prods.length} 款`;
      document.getElementById("kpiEmployeeCount").textContent = `${emps.length} 人`;
      document.getElementById("kpiRmaCount").textContent = `${rmas.filter(r => r.is_fraud_detected).length} 单欺诈拦截`;

      // 渲染产品
      document.getElementById("execProductList").innerHTML = prods.map(p => `
        <div class="list-item-row">
          <div>
            <strong>[${p.bravio_id}] ${p.product_name}</strong>
            <div style="font-size:12px; color:var(--text-muted); margin-top:3px;">
              阶段门: Gate ${p.current_phase_gate} (${p.lifecycle_status}) · KBA: ${p.kba_approval_number || '审核中'}
            </div>
          </div>
          <span class="badge badge-success">${p.category}</span>
        </div>
      `).join("") || "暂无产品";

      // 渲染 8D
      document.getElementById("execEightDList").innerHTML = eightDs.map(e => `
        <div class="list-item-row">
          <div>
            <strong>${e.incident_number} · ${e.title}</strong>
            <div style="font-size:12px; color:var(--text-muted); margin-top:3px;">
              负责专家: ${e.d1_team_leader || '质量工程师'} · 来源: ${e.source}
            </div>
          </div>
          <span class="badge badge-warning">${e.status}</span>
        </div>
      `).join("") || "<div style='color:var(--text-muted); padding:10px;'>暂无重大未结案 8D 客诉</div>";

      // 渲染伙伴
      document.getElementById("execPartnerList").innerHTML = partners.map(pt => `
        <div class="list-item-row">
          <div>
            <strong>[${pt.partner_code}] ${pt.name}</strong>
            <div style="font-size:12px; color:var(--text-muted); margin-top:3px;">
              联系人: ${pt.contact_person || '未设置'} · 账期: Net ${pt.payment_terms_days} 天
            </div>
          </div>
          <span class="badge badge-info">${pt.partner_type}</span>
        </div>
      `).join("") || "暂无伙伴";

      // 渲染 RMA
      document.getElementById("execRmaList").innerHTML = rmas.map(r => `
        <div class="list-item-row">
          <div>
            <strong>${r.rma_number} · 客户: ${r.customer_name}</strong>
            <div style="font-size:12px; color:var(--text-muted); margin-top:3px;">
              退回序列号: ${r.returned_sn.substring(0, 18)}... · 留样架: ${r.sample_location_matched || '慕尼黑A4'}
            </div>
          </div>
          <span class="badge ${r.is_fraud_detected ? 'badge-danger' : 'badge-success'}">
            ${r.is_fraud_detected ? '⚠️ 换盒欺诈拦截' : r.status}
          </span>
        </div>
      `).join("") || "<div style='color:var(--text-muted); padding:10px;'>暂无退货申请</div>";

    } catch (err) {
      console.error("加载总裁办驾驶舱失败:", err);
    }
  }
};
