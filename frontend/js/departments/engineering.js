// 📐 研发与工程技术中心 (R&D & Engineering) - 产品工程师 (PE / 王工程) 核心工作台
window.DepartmentEngineering = {
  currentSub: "products",

  async render(container) {
    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">📐 研发与工程技术中心 (R&D & Engineering)</h2>
          <p class="dept-subtitle">产品工程师工作台：产品主数据、APQP 阶段门管控、多级 BOM 维护、汽车级工程变更 (ECM) 与条码规则引擎 (docs/10~13)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentEngineering.openNewProductModal()">+ 定义新产品料号</button>
        </div>
      </div>

      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnEngProd" onclick="window.DepartmentEngineering.switchSub('products')">📦 产品主数据与 APQP 阶段门 (Doc 10)</button>
        <button class="sub-nav-btn" id="btnEngBom" onclick="window.DepartmentEngineering.switchSub('bom')">🌳 轻量多级 BOM 与出货包装层级 (Doc 11)</button>
        <button class="sub-nav-btn" id="btnEngEcm" onclick="window.DepartmentEngineering.switchSub('ecm')">📋 汽车级工程变更 (ECM / ECO - Doc 13)</button>
        <button class="sub-nav-btn" id="btnEngBarcode" onclick="window.DepartmentEngineering.switchSub('barcode')">🏷️ 多层级条码规则引擎 (Doc 12)</button>
      </div>

      <div id="engSubContent" style="margin-top:16px;"></div>
    `;

    await this.switchSub("products");
  },

  async switchSub(sub) {
    this.currentSub = sub;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const map = { products: 'btnEngProd', bom: 'btnEngBom', ecm: 'btnEngEcm', barcode: 'btnEngBarcode' };
    const bEl = document.getElementById(map[sub]);
    if (bEl) bEl.classList.add("active");

    const content = document.getElementById("engSubContent");
    if (sub === "products") await this.renderProducts(content);
    else if (sub === "bom") await this.renderBom(content);
    else if (sub === "ecm") await this.renderEcm(content);
    else if (sub === "barcode") await this.renderBarcode(content);
  },

  async renderProducts(container) {
    container.innerHTML = `<div class="loading-spinner">正在拉取产品主数据...</div>`;
    try {
      const prods = await ApiClient.get("/products");
      container.innerHTML = `
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Bravio 零件号</th>
                <th>产品名称与规格</th>
                <th>图纸版本</th>
                <th>大类</th>
                <th>KBA 型式认证号</th>
                <th>APQP 阶段门生命周期</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${prods.map(p => `
                <tr>
                  <td>
                    <a class="table-action-link" href="javascript:void(0)" onclick="window.DepartmentEngineering.openProductDetail('${p.id}')">
                      <code>${p.bravio_id}</code>
                    </a>
                  </td>
                  <td>
                    <div style="display:flex; align-items:center; gap:10px;">
                      <img src="${p.primary_image_url || 'assets/demo_images/product_matrix_led.svg'}" style="width:48px; height:36px; border-radius:4px; object-fit:contain; border:1px solid #cbd5e1; background:#090d16; flex-shrink:0;">
                      <a class="table-action-link" href="javascript:void(0)" onclick="window.DepartmentEngineering.openProductDetail('${p.id}')">
                        <strong>${p.product_name}</strong>
                      </a>
                    </div>
                  </td>
                  <td><span class="badge badge-secondary">Rev ${p.current_revision}</span></td>
                  <td>${p.category}</td>
                  <td>${p.kba_approval_number ? `<span class="badge badge-success">✓ ${p.kba_approval_number}</span>` : '<span style="color:var(--text-muted);">申请中</span>'}</td>
                  <td>
                    <span class="badge badge-info">Gate ${p.current_phase_gate}: ${p.lifecycle_status}</span>
                  </td>
                  <td>
                    <div style="display:flex; gap:6px;">
                      <button class="btn-secondary btn-xs" onclick="window.DepartmentEngineering.openProductDetail('${p.id}')">查看/编辑</button>
                      <button class="btn-secondary btn-xs" onclick="window.DepartmentEngineering.advanceGate('${p.id}')">推进阶段门 ➔</button>
                    </div>
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

  async renderBom(container) {
    container.innerHTML = `<div class="loading-spinner">正在展开工程 BOM 与包装层级...</div>`;
    try {
      const prods = await ApiClient.get("/products");
      if (!prods.length) {
        container.innerHTML = `<div class="content-card">暂无产品数据</div>`;
        return;
      }
      const boms = await ApiClient.get(`/boms/product/${prods[0].id}`);
      const bom = boms[0];

      container.innerHTML = `
        <div class="content-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <div>
              <h3>BOM 架构: ${prods[0].product_name} (${bom ? bom.version : 'V1.0'})</h3>
              <p style="color:var(--text-muted); font-size:13px; margin-top:4px;">轻量级四层划分：子总成、零件、成文说明书、吸塑防伪包材 (docs/11)</p>
            </div>
            ${bom && bom.packaging ? `
              <div style="text-align:right;">
                <span class="badge badge-info">📦 每盒: ${bom.packaging.pieces_per_box}支 (一盒双灯)</span>
                <span class="badge badge-info">每箱: ${bom.packaging.boxes_per_carton}盒</span>
                <span class="badge badge-info">每托盘: ${bom.packaging.cartons_per_pallet}箱</span>
              </div>
            ` : ''}
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>物料号</th>
                  <th>物料名称</th>
                  <th>类别</th>
                  <th>用量 (单位)</th>
                  <th>位号 (Designator)</th>
                  <th>关键安全特性</th>
                </tr>
              </thead>
              <tbody>
                ${bom && bom.items ? bom.items.map(it => `
                  <tr>
                    <td><code>${it.part_number}</code></td>
                    <td><strong>${it.part_name}</strong></td>
                    <td><span class="badge badge-secondary">${it.category}</span></td>
                    <td>${it.quantity} ${it.unit}</td>
                    <td><code>${it.reference_designator || '--'}</code></td>
                    <td>${it.is_safety_critical ? '<span class="badge badge-danger">★ 特殊安全特性</span>' : '普通件'}</td>
                  </tr>
                `).join("") : '<tr><td colspan="6">暂无明细</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载失败: ${err.message}</div>`;
    }
  },

  async renderEcm(container) {
    container.innerHTML = `<div class="loading-spinner">正在读取工程变更指令 (ECO)...</div>`;
    try {
      const ecos = await ApiClient.get("/ecm");
      container.innerHTML = `
        <div style="margin-bottom:12px; display:flex; justify-content:flex-end;">
          <button class="btn-primary" onclick="window.DepartmentEngineering.openNewEcoModal()">+ 发起工程设计变更 (ECR/ECO)</button>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ECO 指令号</th>
                <th>变更标题</th>
                <th>变更类型</th>
                <th>影响分析 (图纸/BOM/KBA)</th>
                <th>当前审批流状态</th>
                <th>会签批准人</th>
              </tr>
            </thead>
            <tbody>
              ${ecos.map(ec => `
                <tr>
                  <td><code>${ec.eco_number}</code></td>
                  <td><strong>${ec.title}</strong><div style="font-size:12px; color:var(--text-muted);">${ec.reason}</div></td>
                  <td><span class="badge badge-info">${ec.change_type}</span></td>
                  <td>
                    ${ec.affects_kba_homologation ? '<span class="badge badge-warning">⚠️ 触发KBA型式认证评价</span>' : ''}
                    ${ec.affects_drawings ? '<span class="badge badge-secondary">图纸更新</span>' : ''}
                    ${ec.affects_bom ? '<span class="badge badge-secondary">BOM变更</span>' : ''}
                  </td>
                  <td><span class="badge ${ec.status === 'APPROVED' || ec.status === 'RELEASED' ? 'badge-success' : 'badge-warning'}">${ec.status}</span></td>
                  <td>${ec.approver_name || '待评审会签'}</td>
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

  async renderBarcode(container) {
    container.innerHTML = `
      <div class="grid-2-col">
        <div class="content-card">
          <h3>🏷️ 32位激光微距码与包装条码在线验证</h3>
          <p style="color:var(--text-muted); font-size:13px; margin:8px 0 16px 0;">依据 docs/12 规则引擎，输入零件号与Binning，正向生成32位微距码与逆向解析结构</p>
          <div class="form-group">
            <label class="form-label">Bravio 零件号</label>
            <input type="text" id="bcBravioId" class="form-input" value="99824">
          </div>
          <div class="form-group">
            <label class="form-label">LED Binning 档位参数 (色温-光通-电压)</label>
            <input type="text" id="bcBin" class="form-input" value="6000K-1200LM-12V">
          </div>
          <button class="btn-primary" onclick="window.DepartmentEngineering.testGenerateBarcode()">⚡ 正向生成 32位 激光码</button>
          <div id="bcGenResult" style="margin-top:16px;"></div>
        </div>

        <div class="content-card">
          <h3>🔍 逆向正则全链路解析验真</h3>
          <div class="form-group">
            <label class="form-label">粘贴待检测条码 (SN / BOX / CARTON / PALLET)</label>
            <input type="text" id="bcRawInput" class="form-input" value="99824A2642000001086000K1200LM12">
          </div>
          <button class="btn-secondary" onclick="window.DepartmentEngineering.testParseBarcode()">🔎 逆向解析内部字段</button>
          <div id="bcParseResult" style="margin-top:16px;"></div>
        </div>
      </div>
    `;
  },

  async testGenerateBarcode() {
    const bravio_id = document.getElementById("bcBravioId").value.trim();
    const binning = document.getElementById("bcBin").value.trim();
    try {
      const res = await ApiClient.post("/barcode-rules/generate", {
        level: "SN",
        bravio_id,
        revision: "A",
        sequence: 88,
        binning
      });
      document.getElementById("bcGenResult").innerHTML = `
        <div style="padding:12px; background:#ecfdf5; border:1px solid #10b981; border-radius:6px;">
          <div style="font-size:12px; color:#047857; font-weight:700;">生成成功 (长度: ${res.length} 位):</div>
          <code style="font-size:15px; font-weight:700; color:#065f46; letter-spacing:1px;">${res.barcode}</code>
        </div>
      `;
    } catch (err) {
      alert("生成失败: " + err.message);
    }
  },

  async testParseBarcode() {
    const barcode = document.getElementById("bcRawInput").value.trim();
    try {
      const res = await ApiClient.post("/barcode-rules/parse", { barcode });
      document.getElementById("bcParseResult").innerHTML = `
        <div style="padding:12px; background:#f8fafc; border:1px solid var(--border-color); border-radius:6px;">
          <div>层级判别: <span class="badge badge-info">${res.level}</span> 合规有效: <strong>${res.is_valid}</strong></div>
          <pre style="margin-top:8px; font-size:12px;">${JSON.stringify(res.parsed_fields, null, 2)}</pre>
        </div>
      `;
    } catch (err) {
      alert("解析失败: " + err.message);
    }
  },

  async advanceGate(prodId) {
    try {
      await ApiClient.post(`/products/${prodId}/advance-lifecycle?target_status=MASS_PRODUCTION_SOP`);
      alert("APQP 阶段门推进成功：已达成量产 SOP 阶段！");
      await this.renderProducts(document.getElementById("engSubContent"));
    } catch (err) {
      alert("推进失败: " + err.message);
    }
  },

  openNewProductModal() {
    const existing = document.getElementById("engProdModalOverlay");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "engProdModalOverlay";
    overlay.className = "erp-modal-overlay";
    overlay.innerHTML = `
      <div class="erp-modal-container large" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>📦 定义新车规级产品料号 (ISO 9001 & KBA Type Approval)</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('engProdModalOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <form id="newProdForm" onsubmit="event.preventDefault(); window.DepartmentEngineering.submitNewProduct();">
            <div class="form-grid-2">
              <div class="form-group">
                <label class="form-label">Bravio 5位唯一零件号 *</label>
                <input type="text" id="nprId" class="form-input" placeholder="如 99825" maxlength="10" required>
              </div>
              <div class="form-group">
                <label class="form-label">产品全称与工程规格 *</label>
                <input type="text" id="nprName" class="form-input" placeholder="如 Matrix LED 激光大灯总成 24W" required>
              </div>
            </div>

            <div class="form-grid-3" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">图纸工程版本</label>
                <input type="text" id="nprRev" class="form-input" value="A" required>
              </div>
              <div class="form-group">
                <label class="form-label">产品大类 *</label>
                <select id="nprCat" class="form-select" required>
                  <option value="HEADLIGHT">HEADLIGHT (前照大灯总成)</option>
                  <option value="TAILLIGHT">TAILLIGHT (尾灯总成)</option>
                  <option value="MODULE">MODULE (LED/激光核心光学模组)</option>
                  <option value="PCB">PCB (驱动电源与控制板)</option>
                  <option value="OPTICAL">OPTICAL (透镜与反射光学件)</option>
                  <option value="PACKAGING">PACKAGING (出厂包材总成)</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">质保期 (月数)</label>
                <input type="number" id="nprWarranty" class="form-input" value="24" min="0">
              </div>
            </div>

            <div class="form-grid-2" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">德国 KBA 型式认证号 (ECE Homologation)</label>
                <input type="text" id="nprKba" class="form-input" placeholder="如 E1-149R-001234">
              </div>
              <div class="form-group">
                <label class="form-label">型式认证主管机构</label>
                <input type="text" id="nprAuthority" class="form-input" value="KBA-Flensburg">
              </div>
            </div>

            <div class="form-grid-3" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">ISO 9001 特性分类</label>
                <select id="nprIso" class="form-select">
                  <option value="SAFETY_RELEVANT" selected>SAFETY_RELEVANT (汽车安全关键特性)</option>
                  <option value="STANDARD">STANDARD (常规车规标准件)</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">APQP 初始阶段门</label>
                <select id="nprGate" class="form-select">
                  <option value="1" selected>Gate 1: 立项与可行性</option>
                  <option value="2">Gate 2: 概念与设计开发</option>
                  <option value="3">Gate 3: 过程设计与DVP</option>
                  <option value="4">Gate 4: 试产与PPAP验证</option>
                  <option value="5">Gate 5: 量产SOP交付</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">生命周期状态</label>
                <select id="nprStatus" class="form-select">
                  <option value="PROJECT_KICKOFF" selected>PROJECT_KICKOFF (立项启动)</option>
                  <option value="A_SAMPLE">A_SAMPLE (A样概念验证)</option>
                  <option value="B_SAMPLE">B_SAMPLE (B样工程验证)</option>
                  <option value="PPAP_SIGN_OFF">PPAP_SIGN_OFF (PPAP批准)</option>
                  <option value="MASS_PRODUCTION_SOP">MASS_PRODUCTION_SOP (量产SOP)</option>
                  <option value="END_OF_PRODUCTION_EOP">END_OF_PRODUCTION_EOP (停产归档)</option>
                </select>
              </div>
            </div>

            <div class="form-grid-2" style="margin-top:12px;">
              <div class="form-group">
                <label class="form-label">
                  <input type="checkbox" id="nprCert" checked style="margin-right:6px;">
                  <strong>受控型式认证体系管辖 (Is Certified)</strong>
                </label>
              </div>
              <div class="form-group">
                <label class="form-label">
                  <input type="checkbox" id="nprSerialized" checked style="margin-right:6px;">
                  <strong>32 位激光微距码单品追溯 (Is Serialized)</strong>
                </label>
              </div>
            </div>

            <div class="form-group" style="margin-top:12px;">
              <label class="form-label">工程设计概要与物料技术说明</label>
              <textarea id="nprNotes" class="form-input" rows="2" placeholder="说明设计输入要求、光学仿真指标或特殊防呆装配要求..."></textarea>
            </div>

            <div style="margin-top:18px; display:flex; justify-content:flex-end; gap:10px;">
              <button type="button" class="btn-secondary" onclick="document.getElementById('engProdModalOverlay').remove()">取消</button>
              <button type="submit" id="nprSubmitBtn" class="btn-primary">✓ 定义并生成产品主数据</button>
            </div>
          </form>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  async submitNewProduct() {
    const btn = document.getElementById("nprSubmitBtn");
    btn.disabled = true;
    btn.textContent = "正在创建主数据...";

    const payload = {
      bravio_id: document.getElementById("nprId").value.trim(),
      product_name: document.getElementById("nprName").value.trim(),
      current_revision: document.getElementById("nprRev").value.trim() || "A",
      category: document.getElementById("nprCat").value,
      is_certified: document.getElementById("nprCert").checked,
      kba_approval_number: document.getElementById("nprKba").value.trim() || null,
      homologation_authority: document.getElementById("nprAuthority").value.trim() || "KBA-Flensburg",
      iso_classification: document.getElementById("nprIso").value,
      is_serialized: document.getElementById("nprSerialized").checked,
      standard_warranty_months: parseInt(document.getElementById("nprWarranty").value) || 24,
      lifecycle_status: document.getElementById("nprStatus").value,
      current_phase_gate: parseInt(document.getElementById("nprGate").value) || 1,
      notes: document.getElementById("nprNotes").value.trim() || null
    };

    try {
      const res = await ApiClient.post("/products", payload);
      alert(`🎉 车规级产品料号定义成功！\nBravio 零件号: ${res.bravio_id}\n品名: ${res.product_name}\n图纸版本: Rev ${res.current_revision}`);
      const m = document.getElementById("engProdModalOverlay");
      if (m) m.remove();
      await this.renderProducts(document.getElementById("engSubContent"));
    } catch (err) {
      alert("创建失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✓ 定义并生成产品主数据";
      }
    }
  },

  async openProductDetail(prodId) {
    const existing = document.getElementById("engProdDetailModalOverlay");
    if (existing) existing.remove();

    try {
      const p = await ApiClient.get(`/products/${prodId}`);
      const overlay = document.createElement("div");
      overlay.id = "engProdDetailModalOverlay";
      overlay.className = "erp-modal-overlay";
      overlay.innerHTML = `
        <div class="erp-modal-container large" onclick="event.stopPropagation()">
          <div class="erp-modal-header">
            <div>
              <h3>产品数据详情</h3>
              <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                零件号: <code>${p.bravio_id}</code> · 初始建立: ${p.created_at ? p.created_at.substring(0, 10) : '--'}
              </p>
            </div>
            <button class="erp-modal-close-btn" onclick="document.getElementById('engProdDetailModalOverlay').remove()">✕</button>
          </div>
          <div class="erp-modal-body">
            <!-- 头部基本属性与右上角产品实物图区域 (按需求 2：排版在 UI 卡片显示的右上方位置) -->
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:20px; background:#f8fafc; border:1px solid var(--border-color); border-radius:10px; padding:16px; margin-bottom:16px;">
              <!-- 左侧：产品合规与APQP阶段门状态 -->
              <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                  <span class="badge badge-info" style="font-size:12px;">Gate ${p.current_phase_gate}: ${p.lifecycle_status}</span>
                  <span class="badge ${p.kba_approval_number ? 'badge-success' : 'badge-warning'}">
                    ${p.kba_approval_number ? 'KBA认证: ' + p.kba_approval_number : 'KBA型式认证申请中'}
                  </span>
                  <span class="badge badge-secondary">${p.iso_classification}</span>
                </div>
                <div style="font-size:13px; color:var(--text-muted); line-height:1.6;">
                  <div>物料代码: <code>${p.bravio_id}</code> · 大类: <strong>${p.category}</strong> · 工程版本: <strong>Rev ${p.current_revision}</strong></div>
                  <div>32位激光微距追溯: <strong>${p.is_serialized ? '✓ 已启用 DataMatrix' : '未序列化'}</strong> · 质保周期: <strong>${p.standard_warranty_months || 24} 个月</strong></div>
                  <div>型式认证机构: <strong>${p.homologation_authority || 'KBA-Flensburg'}</strong></div>
                </div>
              </div>

              <!-- 右上方：产品实物/设计图卡片 (排版在卡片右上方) -->
              <div style="width:170px; flex-shrink:0; display:flex; flex-direction:column; align-items:center; text-align:center; padding:10px; background:#ffffff; border:1px solid var(--border-color); border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="width:150px; height:100px; border-radius:6px; overflow:hidden; border:1px solid #cbd5e1; background:#090d16; display:flex; align-items:center; justify-content:center; margin-bottom:8px;">
                  <img id="eprImgPreview" src="${p.primary_image_url || 'assets/demo_images/product_matrix_led.svg'}" style="max-width:100%; max-height:100%; object-fit:contain;">
                </div>
                <div style="font-size:11px; font-weight:700; color:var(--text-muted); margin-bottom:6px;">产品实物 / 设计渲染图</div>
                <div style="display:flex; flex-direction:column; gap:4px; width:100%;">
                  <button type="button" class="btn-secondary btn-xs" style="width:100%; font-size:11px; padding:3px 6px;" onclick="document.getElementById('eprImgFileInput').click()">📷 上传实物图</button>
                  <input type="file" id="eprImgFileInput" accept="image/*" style="display:none;" onchange="window.DepartmentEngineering.handleProductImageUpload('${p.id}', this)">
                  <button type="button" class="btn-secondary btn-xs" style="width:100%; font-size:11px; padding:3px 6px;" onclick="window.DepartmentEngineering.openDemoProductPicker('${p.id}')">✨ 选预置Demo图</button>
                </div>
              </div>
            </div>

            <form id="editProdForm" onsubmit="event.preventDefault(); window.DepartmentEngineering.saveProductChanges('${p.id}');">
              <div class="form-grid-2">
                <div class="form-group">
                  <label class="form-label">产品全称与规格型号 *</label>
                  <input type="text" id="eprName" class="form-input" value="${p.product_name || ''}" required>
                </div>
                <div class="form-group">
                  <label class="form-label">图纸工程修订版本 (Revision) *</label>
                  <input type="text" id="eprRev" class="form-input" value="${p.current_revision || 'A'}" required>
                </div>
              </div>

              <div class="form-grid-3" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">产品大类</label>
                  <select id="eprCat" class="form-select">
                    <option value="HEADLIGHT" ${p.category === 'HEADLIGHT' ? 'selected' : ''}>HEADLIGHT (前照大灯总成)</option>
                    <option value="TAILLIGHT" ${p.category === 'TAILLIGHT' ? 'selected' : ''}>TAILLIGHT (尾灯总成)</option>
                    <option value="MODULE" ${p.category === 'MODULE' ? 'selected' : ''}>MODULE (核心模组)</option>
                    <option value="PCB" ${p.category === 'PCB' ? 'selected' : ''}>PCB (驱动控制板)</option>
                    <option value="OPTICAL" ${p.category === 'OPTICAL' ? 'selected' : ''}>OPTICAL (透镜光学件)</option>
                    <option value="PACKAGING" ${p.category === 'PACKAGING' ? 'selected' : ''}>PACKAGING (出厂包材)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">标准质保月数</label>
                  <input type="number" id="eprWarranty" class="form-input" value="${p.standard_warranty_months || 24}">
                </div>
                <div class="form-group">
                  <label class="form-label">APQP 阶段门 (Phase Gate)</label>
                  <select id="eprGate" class="form-select">
                    <option value="1" ${p.current_phase_gate === 1 ? 'selected' : ''}>Gate 1: 立项可行性</option>
                    <option value="2" ${p.current_phase_gate === 2 ? 'selected' : ''}>Gate 2: 概念与设计开发</option>
                    <option value="3" ${p.current_phase_gate === 3 ? 'selected' : ''}>Gate 3: 过程设计与DVP</option>
                    <option value="4" ${p.current_phase_gate === 4 ? 'selected' : ''}>Gate 4: 试产与PPAP</option>
                    <option value="5" ${p.current_phase_gate === 5 ? 'selected' : ''}>Gate 5: 量产SOP</option>
                  </select>
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">德国 KBA 型式认证号</label>
                  <input type="text" id="eprKba" class="form-input" value="${p.kba_approval_number || ''}">
                </div>
                <div class="form-group">
                  <label class="form-label">认证主管机构</label>
                  <input type="text" id="eprAuthority" class="form-input" value="${p.homologation_authority || 'KBA-Flensburg'}">
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">ISO 9001 特性分类</label>
                  <select id="eprIso" class="form-select">
                    <option value="SAFETY_RELEVANT" ${p.iso_classification === 'SAFETY_RELEVANT' ? 'selected' : ''}>SAFETY_RELEVANT (汽车安全关键特性)</option>
                    <option value="STANDARD" ${p.iso_classification === 'STANDARD' ? 'selected' : ''}>STANDARD (一般车规标准件)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">生命周期状态</label>
                  <select id="eprStatus" class="form-select">
                    <option value="PROJECT_KICKOFF" ${p.lifecycle_status === 'PROJECT_KICKOFF' ? 'selected' : ''}>PROJECT_KICKOFF (立项启动)</option>
                    <option value="A_SAMPLE" ${p.lifecycle_status === 'A_SAMPLE' ? 'selected' : ''}>A_SAMPLE (A样概念验证)</option>
                    <option value="B_SAMPLE" ${p.lifecycle_status === 'B_SAMPLE' ? 'selected' : ''}>B_SAMPLE (B样工程验证)</option>
                    <option value="PPAP_SIGN_OFF" ${p.lifecycle_status === 'PPAP_SIGN_OFF' ? 'selected' : ''}>PPAP_SIGN_OFF (PPAP批准)</option>
                    <option value="MASS_PRODUCTION_SOP" ${p.lifecycle_status === 'MASS_PRODUCTION_SOP' ? 'selected' : ''}>MASS_PRODUCTION_SOP (量产SOP)</option>
                    <option value="END_OF_PRODUCTION_EOP" ${p.lifecycle_status === 'END_OF_PRODUCTION_EOP' ? 'selected' : ''}>END_OF_PRODUCTION_EOP (停产归档)</option>
                  </select>
                </div>
              </div>

              <div class="form-grid-2" style="margin-top:12px;">
                <div class="form-group">
                  <label class="form-label">
                    <input type="checkbox" id="eprCert" ${p.is_certified ? 'checked' : ''} style="margin-right:6px;">
                    <strong>受控型式认证体系管辖</strong>
                  </label>
                </div>
                <div class="form-group">
                  <label class="form-label">
                    <input type="checkbox" id="eprSerialized" ${p.is_serialized ? 'checked' : ''} style="margin-right:6px;">
                    <strong>32 位激光微距码单品追溯</strong>
                  </label>
                </div>
              </div>

              <div class="form-group" style="margin-top:12px;">
                <label class="form-label">工程说明与设计变更备注</label>
                <textarea id="eprNotes" class="form-input" rows="2">${p.notes || ''}</textarea>
              </div>

              <div style="margin-top:18px; display:flex; justify-content:flex-end; gap:10px;">
                <button type="button" class="btn-secondary" onclick="document.getElementById('engProdDetailModalOverlay').remove()">取消</button>
                <button type="submit" id="eprSaveBtn" class="btn-primary">💾 保存修改并同步生效</button>
              </div>
            </form>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    } catch (err) {
      alert("加载产品主数据详情失败: " + err.message);
    }
  },

  async saveProductChanges(prodId) {
    const btn = document.getElementById("eprSaveBtn");
    btn.disabled = true;
    btn.textContent = "正在保存变更...";

    const payload = {
      product_name: document.getElementById("eprName").value.trim(),
      current_revision: document.getElementById("eprRev").value.trim(),
      category: document.getElementById("eprCat").value,
      is_certified: document.getElementById("eprCert").checked,
      kba_approval_number: document.getElementById("eprKba").value.trim() || null,
      homologation_authority: document.getElementById("eprAuthority").value.trim() || "KBA-Flensburg",
      iso_classification: document.getElementById("eprIso").value,
      is_serialized: document.getElementById("eprSerialized").checked,
      standard_warranty_months: parseInt(document.getElementById("eprWarranty").value) || 24,
      current_phase_gate: parseInt(document.getElementById("eprGate").value) || 1,
      lifecycle_status: document.getElementById("eprStatus").value,
      notes: document.getElementById("eprNotes").value.trim() || null
    };

    try {
      await ApiClient.put(`/products/${prodId}`, payload);
      alert("✓ 产品主数据修改成功并已安全落库！");
      const m = document.getElementById("engProdDetailModalOverlay");
      if (m) m.remove();
      await this.renderProducts(document.getElementById("engSubContent"));
    } catch (err) {
      alert("保存失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "💾 保存修改并同步生效";
      }
    }
  },

  openNewEcoModal() {
    alert("正在创建工程变更申请 ECR -> ECO！");
  },

  async handleProductImageUpload(prodId, fileInput) {
    if (!fileInput.files || !fileInput.files[0]) return;
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("res_model", "product_master");
    formData.append("res_id", prodId);
    formData.append("description", `产品实物/设计图上传`);

    try {
      const res = await ApiClient.uploadFormData("/system/attachments/upload", formData);
      const img = document.getElementById("eprImgPreview");
      if (img) img.src = res.file_url + "?t=" + Date.now();
      alert("✓ 产品实物设计图上传并更新成功！");
      await this.renderProducts(document.getElementById("engTabContent"));
    } catch (err) {
      alert("上传产品图失败: " + err.message);
    }
  },

  openDemoProductPicker(prodId) {
    const demos = [
      { file: "product_matrix_led.svg", title: "矩阵大灯总成 (Matrix LED)" },
      { file: "product_drl_module.svg", title: "流水日行灯带 (Dynamic DRL)" },
      { file: "product_taillight_bar.svg", title: "贯穿式OLED尾灯 (Aero Tail)" },
      { file: "product_driver_board.svg", title: "CAN-FD 驱动主板 (ECU Board)" }
    ];

    const pickerOverlay = document.createElement("div");
    pickerOverlay.id = "demoProdPickerOverlay";
    pickerOverlay.className = "erp-modal-overlay";
    pickerOverlay.style.zIndex = "1050";
    pickerOverlay.innerHTML = `
      <div class="erp-modal-container small" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>✨ 选择产品预置 Demo 实物设计图素材</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('demoProdPickerOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:12px; margin-top:8px;">
            ${demos.map(d => `
              <div onclick="window.DepartmentEngineering.selectDemoProduct('${prodId}', '${d.file}')" style="cursor:pointer; border:1px solid var(--border-color); border-radius:8px; padding:10px; text-align:center; transition:all 0.2s;" onmouseover="this.style.borderColor='#3b82f6'; this.style.background='#f0f9ff';" onmouseout="this.style.borderColor='var(--border-color)'; this.style.background='#fff';">
                <div style="width:100%; height:75px; background:#090d16; border-radius:4px; overflow:hidden; display:flex; align-items:center; justify-content:center; margin-bottom:6px;">
                  <img src="assets/demo_images/${d.file}" style="max-width:100%; max-height:100%; object-fit:contain;">
                </div>
                <div style="font-size:11.5px; font-weight:700; color:var(--text-main);">${d.title}</div>
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(pickerOverlay);
  },

  async selectDemoProduct(prodId, demoFile) {
    try {
      const res = await ApiClient.post("/system/attachments/bind-demo", {
        res_model: "product_master",
        res_id: prodId,
        demo_filename: demoFile,
        description: `选用预置Demo产品图: ${demoFile}`
      });
      const img = document.getElementById("eprImgPreview");
      if (img) img.src = res.file_url + "?t=" + Date.now();
      const p = document.getElementById("demoProdPickerOverlay");
      if (p) p.remove();
      alert("✓ 已成功切换为预置 Demo 产品实物图！");
      await this.renderProducts(document.getElementById("engTabContent"));
    } catch (err) {
      alert("绑定预置产品图失败: " + err.message);
    }
  }
};
