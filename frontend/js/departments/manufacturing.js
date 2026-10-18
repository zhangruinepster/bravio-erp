// 🏭 制造与供应链协同中心 (Manufacturing & SCM) - 供应商专员 (Supplier / 张供应) 核心工作台
window.DepartmentManufacturing = {
  currentSub: "partners",

  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">🏭 制造与供应链协同中心 (Manufacturing & SCM)</h2>
          <p class="dept-subtitle">商业伙伴管理、B2B 外协代工任务、车间 32 位激光打码与一盒双灯配对防呆执行工位 (docs/07, 16 & 17)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentManufacturing.openNewPartnerModal()">+ 登记商业伙伴</button>
        </div>
      </div>

      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnMfgPartner" onclick="window.DepartmentManufacturing.switchSub('partners')">🤝 商业伙伴档案 (供应商/代工厂/客户 - Doc 17)</button>
        <button class="sub-nav-btn" id="btnMfgB2b" onclick="window.DepartmentManufacturing.switchSub('b2b')">📡 B2B 外协代工工单与条码预分配 (Doc 16)</button>
        <button class="sub-nav-btn" id="btnMfgPairing" onclick="window.DepartmentManufacturing.switchSub('pairing')">⚡ 车间工位：一盒双支防呆比对操作台 (Doc 07)</button>
      </div>

      <div id="mfgSubContent" style="margin-top:16px;"></div>
    `;

    await this.switchSub("partners");
  },

  async switchSub(sub) {
    this.currentSub = sub;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const map = { partners: 'btnMfgPartner', b2b: 'btnMfgB2b', pairing: 'btnMfgPairing' };
    const bEl = document.getElementById(map[sub]);
    if (bEl) bEl.classList.add("active");

    const content = document.getElementById("mfgSubContent");
    if (sub === "partners") await this.renderPartners(content);
    else if (sub === "b2b") await this.renderB2b(content);
    else if (sub === "pairing") await this.renderPairingStation(content);
  },

  async renderPartners(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取商业伙伴档案...</div>`;
    try {
      const pts = await ApiClient.get("/partners");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>伙伴编码</th>
                <th>企业名称</th>
                <th>业务类型</th>
                <th>联系人 / 邮箱</th>
                <th>车规代工资质</th>
                <th>账期结算条款</th>
                <th>发货送货网点</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${pts.map(p => `
                <tr>
                  <td><code>${p.partner_code}</code></td>
                  <td>
                    <a class="table-action-link" href="javascript:void(0)" onclick="window.DepartmentManufacturing.openPartnerDetail('${p.id}')">
                      <strong>${p.name}</strong>
                    </a>
                  </td>
                  <td><span class="badge badge-info">${p.partner_type}</span></td>
                  <td>${p.contact_person || '未设置'} (${p.contact_email || '--'})</td>
                  <td>${p.is_oem_certified ? '<span class="badge badge-success">✓ 车规代工已准入</span>' : '<span style="color:var(--text-muted);">免认证</span>'}</td>
                  <td>Net ${p.payment_terms_days} 天</td>
                  <td><small style="color:var(--text-muted);">${p.shipping_address || '未指定'}</small></td>
                  <td>
                    <button class="btn-secondary btn-xs" onclick="window.DepartmentManufacturing.openPartnerDetail('${p.id}')">查看/编辑</button>
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

  async renderB2b(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取外部代工任务...</div>`;
    try {
      const orders = await ApiClient.get("/b2b/work-orders");
      container.innerHTML = `
        <div style="margin-bottom:12px; display:flex; justify-content:flex-end;">
          <button class="btn-primary" onclick="window.DepartmentManufacturing.openNewWoModal()">+ 下达外协代工工单</button>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>工单号</th>
                <th>目标料号</th>
                <th>计划生产数</th>
                <th>预分配条码起始段</th>
                <th>预分配条码截止段</th>
                <th>代工协同状态</th>
                <th>执行备注</th>
              </tr>
            </thead>
            <tbody>
              ${orders.map(o => `
                <tr>
                  <td><code>${o.order_number}</code></td>
                  <td><strong>${o.bravio_id}</strong></td>
                  <td>${o.planned_quantity} 支</td>
                  <td><code>${o.sn_range_start || '--'}</code></td>
                  <td><code>${o.sn_range_end || '--'}</code></td>
                  <td><span class="badge badge-success">${o.status}</span></td>
                  <td><small style="color:var(--text-muted);">${o.notes || '正常生产'}</small></td>
                </tr>
              `).join("") || '<tr><td colspan="7">暂无代工工单</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderPairingStation(container) {
    container.innerHTML = `
      <div class="content-card" style="border-top:4px solid var(--primary);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h3>🏭 包装线一盒双支配对防呆工位 (Poka-Yoke Station - docs/07)</h3>
            <p style="color:var(--text-muted); font-size:13px; margin-top:4px;">
              强制校验：两支车灯色温 (CCT)、光通量 (Lumen)、正向电压 (Vf) 必须 100% 同档位，方可封盒贴标！
            </p>
          </div>
          <span class="badge badge-success">✓ 防呆状态机就绪</span>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:20px;">
          <div class="form-group">
            <label class="form-label">待封装彩盒标签码 (BOX Code)</label>
            <input type="text" id="pairBoxInput" class="form-input" value="BOX-99824-2642-000888">
          </div>
          <div class="form-group">
            <label class="form-label">工位编号</label>
            <input type="text" class="form-input" value="STATION-PACK-01" readonly style="background:#f1f5f9;">
          </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
          <div class="form-group">
            <label class="form-label">第一支单品激光微距序列号 (32位 SN)</label>
            <input type="text" id="pairSn1" class="form-input" placeholder="扫码录入第一支，如 99824A2642000001086000K1200LM12">
          </div>
          <div class="form-group">
            <label class="form-label">第二支单品激光微距序列号 (32位 SN)</label>
            <input type="text" id="pairSn2" class="form-input" placeholder="扫码录入第二支，如 99824A2642000001096000K1200LM12">
          </div>
        </div>

        <div style="margin-top:16px; display:flex; gap:12px;">
          <button class="btn-primary" onclick="window.DepartmentManufacturing.executePairingCheck()">⚡ 触发双灯防呆合规比对</button>
          <button class="btn-secondary" onclick="window.DepartmentManufacturing.fillPairingDemo()">🧪 填充模拟同档双灯</button>
        </div>

        <div id="pairingFeedbackBox" style="margin-top:20px;"></div>
      </div>
    `;
  },

  async fillPairingDemo() {
    try {
      // 快速自动烧录两支同档激光码
      const p1 = await ApiClient.post("/traceability/laser-codes", {
        product_id: "mock",
        bravio_id: "99824",
        revision: "A",
        sequence_int: Math.floor(Math.random() * 900000) + 10000,
        color_temp_bin: "6000K",
        flux_bin: "1200LM",
        voltage_bin: "12V"
      });
      const p2 = await ApiClient.post("/traceability/laser-codes", {
        product_id: "mock",
        bravio_id: "99824",
        revision: "A",
        sequence_int: Math.floor(Math.random() * 900000) + 10000,
        color_temp_bin: "6000K",
        flux_bin: "1200LM",
        voltage_bin: "12V"
      });
      document.getElementById("pairSn1").value = p1.serial_number;
      document.getElementById("pairSn2").value = p2.serial_number;
    } catch (err) {
      alert("填充失败: " + err.message);
    }
  },

  async executePairingCheck() {
    const box_barcode = document.getElementById("pairBoxInput").value.trim();
    const sn_first = document.getElementById("pairSn1").value.trim();
    const sn_second = document.getElementById("pairSn2").value.trim();
    const fb = document.getElementById("pairingFeedbackBox");

    if (!sn_first || !sn_second) {
      alert("请完整输入或扫描两支车灯的 32 位激光微距序列号！");
      return;
    }

    try {
      const res = await ApiClient.post("/traceability/pairing/check-box", {
        box_barcode,
        sn_first,
        sn_second
      });

      if (res.is_pass) {
        fb.innerHTML = `
          <div style="padding:16px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px;">
            <div style="font-size:18px; font-weight:700; color:#047857;">${res.message}</div>
            <div style="margin-top:8px; font-size:13px; color:#065f46;">
              第一支档位: <code>${res.first_bin}</code> | 第二支档位: <code>${res.second_bin}</code> (100% 吻合)
            </div>
          </div>
        `;
      } else {
        fb.innerHTML = `
          <div style="padding:16px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; animation:shake 0.3s;">
            <div style="font-size:18px; font-weight:700; color:#b91c1c;">${res.message}</div>
            <div style="margin-top:8px; font-size:13px; color:#7f1d1d;">
              第一支档位: <code>${res.first_bin}</code> vs 第二支档位: <code>${res.second_bin}</code>
            </div>
          </div>
        `;
      }
    } catch (err) {
      fb.innerHTML = `<div class="auth-alert error">工位比对异常: ${err.message}</div>`;
    }
  },

  openNewPartnerModal() {
    const existing = document.getElementById("mfgPartnerModalOverlay");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "mfgPartnerModalOverlay";
    overlay.className = "erp-modal-overlay";
    overlay.innerHTML = `
      <div class="erp-modal-container large" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>🤝 登记新商业伙伴档案 (供应商 / 代工厂 / 客户)</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('mfgPartnerModalOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <form id="newPartnerForm" onsubmit="event.preventDefault(); window.DepartmentManufacturing.submitNewPartner();">
            <div class="form-grid-2">
              <div class="form-group">
                <label class="form-label">商业伙伴统一编码 *</label>
                <input type="text" id="npCode" class="form-input" placeholder="如 SUP-OEM-02 或 CUST-AUDI-01" required>
              </div>
              <div class="form-group">
                <label class="form-label">企业全称 *</label>
                <input type="text" id="npName" class="form-input" placeholder="如 慕尼黑车规光电制造股份有限公司" required>
              </div>
            </div>

            <div class="form-grid-2" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">业务类型 *</label>
                <select id="npType" class="form-select" required>
                  <option value="SUPPLIER">SUPPLIER (供应链供应商 / 车规委外代工厂)</option>
                  <option value="CUSTOMER">CUSTOMER (汽车主机厂 / 渠道采购客户)</option>
                  <option value="BOTH">BOTH (供销双重身份伙伴)</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">账期结算条款 (天数) *</label>
                <input type="number" id="npTerms" class="form-input" value="60" min="0" required>
              </div>
            </div>

            <div class="form-grid-3" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">主要联系人</label>
                <input type="text" id="npContact" class="form-input" placeholder="如 Hans Weber">
              </div>
              <div class="form-group">
                <label class="form-label">联系工作邮箱</label>
                <input type="email" id="npEmail" class="form-input" placeholder="如 contact@partner.de">
              </div>
              <div class="form-group">
                <label class="form-label">联系电话</label>
                <input type="text" id="npPhone" class="form-input" placeholder="如 +49 89 55443322">
              </div>
            </div>

            <div class="form-group" style="margin-top:12px;">
              <label class="form-label">发货与送货网点地址</label>
              <input type="text" id="npAddress" class="form-input" placeholder="如 München TechPark West, Gate 4, Bavaria, Germany">
            </div>

            <div class="form-group" style="margin-top:12px;">
              <label class="form-label">
                <input type="checkbox" id="npCertified" style="margin-right:6px;">
                <strong>车规 OEM / Tier-1 制造资质认证</strong> (已通过 ISO/TS 16949 与德国 KBA 生产一致性审查)
              </label>
            </div>

            <div class="form-group" style="margin-top:12px;">
              <label class="form-label">业务合作备注与技术档案说明</label>
              <textarea id="npNotes" class="form-input" rows="2" placeholder="填写技术供货范围、M2M API 密钥对接要求或特殊特性协约..."></textarea>
            </div>

            <div style="margin-top:16px; display:flex; justify-content:flex-end; gap:10px;">
              <button type="button" class="btn-secondary" onclick="document.getElementById('mfgPartnerModalOverlay').remove()">取消</button>
              <button type="submit" id="npSubmitBtn" class="btn-primary">✓ 登记并自动生成 M2M Token</button>
            </div>
          </form>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  async submitNewPartner() {
    const btn = document.getElementById("npSubmitBtn");
    btn.disabled = true;
    btn.textContent = "正在提交登记...";

    const payload = {
      partner_code: document.getElementById("npCode").value.trim(),
      name: document.getElementById("npName").value.trim(),
      partner_type: document.getElementById("npType").value,
      contact_person: document.getElementById("npContact").value.trim() || null,
      contact_email: document.getElementById("npEmail").value.trim() || null,
      contact_phone: document.getElementById("npPhone").value.trim() || null,
      payment_terms_days: parseInt(document.getElementById("npTerms").value) || 60,
      shipping_address: document.getElementById("npAddress").value.trim() || null,
      is_oem_certified: document.getElementById("npCertified").checked,
      is_active: true,
      notes: document.getElementById("npNotes").value.trim() || null
    };

    try {
      const res = await ApiClient.post("/partners", payload);
      alert(`🎉 商业伙伴登记成功！\n编码: ${res.partner_code}\n企业: ${res.name}\n已自动生成 M2M 交换 Token: ${res.api_token}`);
      const m = document.getElementById("mfgPartnerModalOverlay");
      if (m) m.remove();
      await this.renderPartners(document.getElementById("mfgSubContent"));
    } catch (err) {
      alert("登记失败: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "✓ 登记并自动生成 M2M Token";
    }
  },

  async openPartnerDetail(partnerId) {
    const existing = document.getElementById("mfgPartnerDetailModalOverlay");
    if (existing) existing.remove();

    try {
      const p = await ApiClient.get(`/partners/${partnerId}`);
      const overlay = document.createElement("div");
      overlay.id = "mfgPartnerDetailModalOverlay";
      overlay.className = "erp-modal-overlay";
      overlay.innerHTML = `
        <div class="erp-modal-container large" onclick="event.stopPropagation()">
          <div class="erp-modal-header">
            <div>
              <h3>🏢 商业伙伴档案详情与参数维护</h3>
              <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                伙伴编号: <code>${p.partner_code}</code> · 建立于: ${p.created_at.substring(0, 10)}
              </p>
            </div>
            <button class="erp-modal-close-btn" onclick="document.getElementById('mfgPartnerDetailModalOverlay').remove()">✕</button>
          </div>
          <div class="erp-modal-body">
            <!-- M2M 机器集成令牌展示 -->
            <div style="padding:10px 14px; background:#f1f5f9; border-radius:8px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <span style="font-size:12px; font-weight:700; color:var(--text-muted);">B2B / M2M 数据交换安全令牌 (API Token):</span>
                <div style="font-family:monospace; font-size:12px; margin-top:2px; word-break:break-all;">${p.api_token || '未分配'}</div>
              </div>
              <button class="btn-secondary btn-xs" onclick="navigator.clipboard.writeText('${p.api_token || ''}'); alert('令牌已复制到剪贴板！');">复制 Token</button>
            </div>

            <form id="editPartnerForm" onsubmit="event.preventDefault(); window.DepartmentManufacturing.savePartnerChanges('${p.id}');">
              <div class="form-grid-2">
                <div class="form-group">
                  <label class="form-label">企业全称 *</label>
                  <input type="text" id="epName" class="form-input" value="${p.name || ''}" required>
                </div>
                <div class="form-group">
                  <label class="form-label">业务类型 *</label>
                  <select id="epType" class="form-select" required>
                    <option value="SUPPLIER" ${p.partner_type === 'SUPPLIER' ? 'selected' : ''}>SUPPLIER (供应链供应商 / 车规代工厂)</option>
                    <option value="CUSTOMER" ${p.partner_type === 'CUSTOMER' ? 'selected' : ''}>CUSTOMER (汽车主机厂 / 渠道客户)</option>
                    <option value="BOTH" ${p.partner_type === 'BOTH' ? 'selected' : ''}>BOTH (供销双重身份伙伴)</option>
                  </select>
                </div>
              </div>

              <div class="form-grid-3" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">联系人</label>
                  <input type="text" id="epContact" class="form-input" value="${p.contact_person || ''}">
                </div>
                <div class="form-group">
                  <label class="form-label">工作邮箱</label>
                  <input type="email" id="epEmail" class="form-input" value="${p.contact_email || ''}">
                </div>
                <div class="form-group">
                  <label class="form-label">联系电话</label>
                  <input type="text" id="epPhone" class="form-input" value="${p.contact_phone || ''}">
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">账期结算条款 (天数)</label>
                  <input type="number" id="epTerms" class="form-input" value="${p.payment_terms_days || 60}">
                </div>
                <div class="form-group">
                  <label class="form-label">发货送货网点</label>
                  <input type="text" id="epAddress" class="form-input" value="${p.shipping_address || ''}">
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">
                    <input type="checkbox" id="epCertified" ${p.is_oem_certified ? 'checked' : ''} style="margin-right:6px;">
                    <strong>车规代工资质准入</strong>
                  </label>
                </div>
                <div class="form-group">
                  <label class="form-label">
                    <input type="checkbox" id="epActive" ${p.is_active ? 'checked' : ''} style="margin-right:6px;">
                    <strong>启用合作状态 (Active)</strong>
                  </label>
                </div>
              </div>

              <div class="form-group" style="margin-top:12px;">
                <label class="form-label">商务合作备注说明</label>
                <textarea id="epNotes" class="form-input" rows="2">${p.notes || ''}</textarea>
              </div>

              <div style="margin-top:16px; display:flex; justify-content:flex-end; gap:10px;">
                <button type="button" class="btn-secondary" onclick="document.getElementById('mfgPartnerDetailModalOverlay').remove()">取消</button>
                <button type="submit" id="epSaveBtn" class="btn-primary">💾 保存修改并同步生效</button>
              </div>
            </form>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    } catch (err) {
      alert("加载商业伙伴详情失败: " + err.message);
    }
  },

  async savePartnerChanges(partnerId) {
    const btn = document.getElementById("epSaveBtn");
    btn.disabled = true;
    btn.textContent = "正在保存变更...";

    const payload = {
      name: document.getElementById("epName").value.trim(),
      partner_type: document.getElementById("epType").value,
      contact_person: document.getElementById("epContact").value.trim() || null,
      contact_email: document.getElementById("epEmail").value.trim() || null,
      contact_phone: document.getElementById("epPhone").value.trim() || null,
      payment_terms_days: parseInt(document.getElementById("epTerms").value) || 60,
      shipping_address: document.getElementById("epAddress").value.trim() || null,
      is_oem_certified: document.getElementById("epCertified").checked,
      is_active: document.getElementById("epActive").checked,
      notes: document.getElementById("epNotes").value.trim() || null
    };

    try {
      await ApiClient.put(`/partners/${partnerId}`, payload);
      alert("✓ 商业伙伴档案修改成功并已安全落库！");
      const m = document.getElementById("mfgPartnerDetailModalOverlay");
      if (m) m.remove();
      await this.renderPartners(document.getElementById("mfgSubContent"));
    } catch (err) {
      alert("保存失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "💾 保存修改并同步生效";
      }
    }
  },

  openNewWoModal() {
    alert("正在下达外部代工任务！");
  }
};
