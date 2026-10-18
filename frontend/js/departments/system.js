// 🛠️ 数字化与运维安全中心 (System Administration & DB Inspector) - 仅限系统总管理员 (Admin) 专享
window.DepartmentSystem = {
  currentSub: "inspector",
  allTables: [],
  currentTable: "product_masters",
  currentPage: 1,
  currentPageSize: 20,
  currentSearch: "",
  cachedTableData: null,
  tableFilterText: "",

  async render(container) {
    const user = AuthService.getCurrentUser();
    if (!AuthService.isSuperAdmin(user)) {
      container.innerHTML = `
        <div class="content-card" style="border-left:4px solid var(--danger); margin-top:20px;">
          <h3 style="color:var(--danger);">⛔ 安全权限阻断 (Access Forbidden)</h3>
          <p style="margin-top:8px; line-height:1.6;">
            当前登录角色 <strong>[${AuthService.getRoleBadge(user)}]</strong> 仅拥有企业业务层权限。<br>
            依据内控与合规审计规范，底层数据库全量探针检视、事务快照控制、灾备回滚与实时日志流仅限【系统总管理员 (Admin)】独占访问！
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="dept-header">
        <div>
          <h2 class="dept-title">🛠️ 数字化与维运安全中心 (DevOps & Database Inspector)</h2>
          <p class="dept-subtitle">系统总管理员专享：数据库实时全景探针、单表行级检视、事务快照与防篡改日志 (docs/05)</p>
        </div>
        <div class="dept-actions">
          <button class="btn-primary" onclick="window.DepartmentSystem.triggerManualSnapshot()">💾 触发数据库一致性快照</button>
        </div>
      </div>

      <!-- 选项卡导航 -->
      <div class="sub-nav-tabs">
        <button class="sub-nav-btn active" id="btnSysInspector" onclick="window.DepartmentSystem.switchSub('inspector')">🗄️ 数据库实时全景与内容探针 (Database Inspector)</button>
        <button class="sub-nav-btn" id="btnSysAttachments" onclick="window.DepartmentSystem.switchSub('attachments')">📁 全局附件与多媒体管理 (Doc 15)</button>
        <button class="sub-nav-btn" id="btnSysBackup" onclick="window.DepartmentSystem.switchSub('backup')">💾 数据库事务快照与安全回滚 (Doc 05)</button>
        <button class="sub-nav-btn" id="btnSysLogs" onclick="window.DepartmentSystem.switchSub('logs')">📡 开发者实时系统日志流捕获</button>
      </div>

      <div id="systemSubContent" style="margin-top:16px;"></div>
    `;

    await this.switchSub("inspector");
  },

  async switchSub(sub) {
    this.currentSub = sub;
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active"));
    const map = { inspector: "btnSysInspector", attachments: "btnSysAttachments", backup: "btnSysBackup", logs: "btnSysLogs" };
    const btn = document.getElementById(map[sub]);
    if (btn) btn.classList.add("active");

    const content = document.getElementById("systemSubContent");
    if (sub === "inspector") {
      await this.renderDbInspector(content);
    } else if (sub === "attachments") {
      await this.renderAttachmentsView(content);
    } else if (sub === "backup") {
      await this.renderBackupsView(content);
    } else if (sub === "logs") {
      await this.renderLogsView(content);
    }
  },

  // =========================================================================
  // 🗄️ 1. 绝对专业的数据库实时全景与内容探针 (Database Inspector)
  // =========================================================================
  async renderDbInspector(container) {
    container.innerHTML = `<div class="loading-spinner">正在探针连接数据库持久层架构...</div>`;
    try {
      const dbMeta = await ApiClient.get("/system/db/tables");
      this.allTables = dbMeta.tables || [];

      // 默认选中
      if (!this.allTables.find(t => t.table_name === this.currentTable) && this.allTables.length > 0) {
        this.currentTable = this.allTables[0].table_name;
      }

      container.innerHTML = `
        <!-- 统计面板 -->
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:16px;">
          <div class="content-card" style="padding:14px 18px;">
            <div style="font-size:11.5px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">持久化数据库内核</div>
            <div style="font-size:16px; font-weight:800; color:var(--text-main); margin-top:4px;">${dbMeta.database_engine}</div>
          </div>
          <div class="content-card" style="padding:14px 18px;">
            <div style="font-size:11.5px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">已注册合规数据表</div>
            <div style="font-size:18px; font-weight:800; color:var(--primary); margin-top:4px;">${dbMeta.total_tables} <span style="font-size:12px; font-weight:normal; color:var(--text-muted);">张表</span></div>
          </div>
          <div class="content-card" style="padding:14px 18px;">
            <div style="font-size:11.5px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">全库当前物化记录数</div>
            <div style="font-size:18px; font-weight:800; color:var(--success); margin-top:4px;">${dbMeta.total_records.toLocaleString()} <span style="font-size:12px; font-weight:normal; color:var(--text-muted);">行</span></div>
          </div>
          <div class="content-card" style="padding:14px 18px;">
            <div style="font-size:11.5px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">一致性防护规范</div>
            <div style="font-size:14px; font-weight:700; color:#0284c7; margin-top:6px;">ACID WAL + 乐观版本锁</div>
          </div>
        </div>

        <!-- 探针双栏布局 -->
        <div class="db-inspector-layout">
          <!-- 左侧：数据表目录与检索 -->
          <div class="db-sidebar-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <strong style="font-size:13.5px; color:var(--text-main);">🗂️ 数据表索引 (${this.allTables.length})</strong>
              <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.renderDbInspector(document.getElementById('systemSubContent'))">🔄</button>
            </div>
            <div style="margin-bottom:10px;">
              <input type="text" id="dbTableFilterInput" class="form-input" style="padding:6px 10px; font-size:12px;" placeholder="快速过滤数据表..." oninput="window.DepartmentSystem.filterTables(this.value)">
            </div>
            <div id="dbTableListContainer" style="overflow-y:auto; flex:1; padding-right:4px;">
              ${this.buildTableListHtml(this.allTables)}
            </div>
          </div>

          <!-- 右侧：选定表的详细内容网格与操作台 -->
          <div class="db-content-card" id="dbTableDataPanel">
            正在载入当前表数据...
          </div>
        </div>
      `;

      await this.loadSelectedTableData();
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载数据库元数据失败: ${err.message}</div>`;
    }
  },

  buildTableListHtml(tables) {
    return tables.map(t => `
      <div class="db-table-item ${t.table_name === this.currentTable ? 'active' : ''}" onclick="window.DepartmentSystem.selectTable('${t.table_name}')">
        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
          <div style="font-weight:700;">${t.display_name}</div>
          <div style="font-family:monospace; font-size:11px; color:var(--text-muted);">${t.table_name}</div>
        </div>
        <span class="badge ${t.row_count > 0 ? 'badge-info' : 'badge-secondary'}" style="font-size:10.5px; padding:2px 6px;">${t.row_count}</span>
      </div>
    `).join("");
  },

  filterTables(keyword) {
    const kw = keyword.toLowerCase().trim();
    const filtered = this.allTables.filter(t => 
      t.table_name.toLowerCase().includes(kw) || 
      (t.display_name && t.display_name.toLowerCase().includes(kw)) ||
      (t.category && t.category.toLowerCase().includes(kw))
    );
    const box = document.getElementById("dbTableListContainer");
    if (box) box.innerHTML = this.buildTableListHtml(filtered);
  },

  async selectTable(tableName) {
    this.currentTable = tableName;
    this.currentPage = 1;
    this.currentSearch = "";
    document.querySelectorAll(".db-table-item").forEach(el => el.classList.remove("active"));
    const activeEl = Array.from(document.querySelectorAll(".db-table-item")).find(el => el.innerText.includes(tableName));
    if (activeEl) activeEl.classList.add("active");

    await this.loadSelectedTableData();
  },

  async loadSelectedTableData() {
    const panel = document.getElementById("dbTableDataPanel");
    if (!panel) return;
    panel.innerHTML = `<div class="loading-spinner">正在查询数据表 [${this.currentTable}] 内容...</div>`;

    try {
      const url = `/system/db/tables/${this.currentTable}/data?page=${this.currentPage}&page_size=${this.currentPageSize}${this.currentSearch ? `&search=${encodeURIComponent(this.currentSearch)}` : ''}`;
      const data = await ApiClient.get(url);
      this.cachedTableData = data;

      panel.innerHTML = `
        <!-- 表头信息与快速操作 -->
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--border-color);">
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <h3 style="font-size:16px; font-weight:800; color:var(--text-main);">${data.display_name}</h3>
              <code>${data.table_name}</code>
              <span class="badge badge-secondary">${data.category}</span>
            </div>
            <p style="font-size:12px; color:var(--text-muted); margin-top:4px;">
              共检索到 <strong>${data.total_rows}</strong> 条记录 · 包含 <strong>${data.columns.length}</strong> 个数据字段 (包含主键与审计追踪列)
            </p>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.loadSelectedTableData()">🔄 刷新数据</button>
            <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.exportCurrentTableCsv()">📥 导出 CSV</button>
            <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.openSchemaModal()">📋 表结构 Schema</button>
          </div>
        </div>

        <!-- 检索与分页工具条 -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:12px; flex-wrap:wrap;">
          <div style="display:flex; gap:8px; align-items:center;">
            <input type="text" id="dbDataSearchInput" class="form-input" style="padding:5px 10px; font-size:12px; width:220px;" placeholder="关键字全文检索..." value="${this.currentSearch}">
            <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.applySearch()">检索</button>
            ${this.currentSearch ? `<button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.clearSearch()">清空</button>` : ''}
          </div>

          <div style="display:flex; align-items:center; gap:8px; font-size:12px;">
            <span>每页:</span>
            <select class="form-select" style="padding:4px 8px; font-size:12px; width:auto;" onchange="window.DepartmentSystem.changePageSize(this.value)">
              <option value="10" ${this.currentPageSize === 10 ? 'selected' : ''}>10 行</option>
              <option value="20" ${this.currentPageSize === 20 ? 'selected' : ''}>20 行</option>
              <option value="50" ${this.currentPageSize === 50 ? 'selected' : ''}>50 行</option>
              <option value="100" ${this.currentPageSize === 100 ? 'selected' : ''}>100 行</option>
            </select>
            <span style="color:var(--text-muted);">第 ${data.page} / ${data.total_pages} 页</span>
            <button class="btn-secondary btn-xs" ${data.page <= 1 ? 'disabled style="opacity:0.5;"' : ''} onclick="window.DepartmentSystem.changePage(${data.page - 1})">◀ 上一页</button>
            <button class="btn-secondary btn-xs" ${data.page >= data.total_pages ? 'disabled style="opacity:0.5;"' : ''} onclick="window.DepartmentSystem.changePage(${data.page + 1})">下一页 ▶</button>
          </div>
        </div>

        <!-- 数据网格视图 (横向自适应滚动) -->
        <div style="overflow-x:auto; flex:1; max-height:490px; border:1px solid var(--border-color); border-radius:6px;">
          <table class="db-data-table">
            <thead>
              <tr>
                <th style="width:40px; text-align:center;">#</th>
                <th style="width:70px;">操作</th>
                ${data.columns.map(c => `
                  <th>
                    ${c.primary_key ? '<span title="主键列" style="color:var(--warning); margin-right:2px;">🔑</span>' : ''}
                    ${c.name}
                    <small style="font-weight:normal; font-size:10px; color:var(--text-muted); display:block;">${c.type}</small>
                  </th>
                `).join("")}
              </tr>
            </thead>
            <tbody>
              ${data.rows.map((row, idx) => `
                <tr>
                  <td style="text-align:center; color:var(--text-muted); font-size:11px;">${(data.page - 1) * data.page_size + idx + 1}</td>
                  <td>
                    <button class="btn-secondary btn-xs" style="padding:2px 6px; font-size:11px;" onclick="window.DepartmentSystem.openRowJsonModal(${idx})">🔍 JSON</button>
                  </td>
                  ${data.columns.map(c => {
                    const val = row[c.name];
                    if (val === null || val === undefined) {
                      return `<td><span style="color:var(--text-muted); font-style:italic;">NULL</span></td>`;
                    }
                    if (typeof val === "boolean") {
                      return `<td>${val ? '<span class="badge badge-success" style="font-size:10px;">✓ TRUE</span>' : '<span class="badge badge-secondary" style="font-size:10px;">✕ FALSE</span>'}</td>`;
                    }
                    if (typeof val === "string" && val.includes("Argon2id Hash Protected")) {
                      return `<td><span style="color:#d97706; font-family:monospace; font-size:11px;">🔒 ${val}</span></td>`;
                    }
                    if (c.primary_key || (typeof val === "string" && val.length === 36 && val.includes("-"))) {
                      return `<td><code>${val}</code></td>`;
                    }
                    return `<td title="${String(val).replace(/"/g, '&quot;')}">${String(val)}</td>`;
                  }).join("")}
                </tr>
              `).join("")}
              ${data.rows.length === 0 ? `<tr><td colspan="${data.columns.length + 2}" style="text-align:center; padding:32px; color:var(--text-muted);">暂无匹配数据记录</td></tr>` : ''}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      panel.innerHTML = `<div class="auth-alert error">加载单表数据失败: ${err.message}</div>`;
    }
  },

  applySearch() {
    const input = document.getElementById("dbDataSearchInput");
    this.currentSearch = input ? input.value.trim() : "";
    this.currentPage = 1;
    this.loadSelectedTableData();
  },

  clearSearch() {
    this.currentSearch = "";
    this.currentPage = 1;
    this.loadSelectedTableData();
  },

  changePage(newPage) {
    this.currentPage = newPage;
    this.loadSelectedTableData();
  },

  changePageSize(newSize) {
    this.currentPageSize = parseInt(newSize);
    this.currentPage = 1;
    this.loadSelectedTableData();
  },

  openRowJsonModal(rowIdx) {
    if (!this.cachedTableData || !this.cachedTableData.rows[rowIdx]) return;
    const row = this.cachedTableData.rows[rowIdx];

    const overlay = document.createElement("div");
    overlay.className = "erp-modal-overlay";
    overlay.id = "dbRowJsonModal";
    overlay.innerHTML = `
      <div class="erp-modal-container large" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>🔍 记录原生行级元数据检视 (Raw Row JSON Preview)</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('dbRowJsonModal').remove()">✕</button>
        </div>
        <div class="erp-modal-body" style="background:#090d16; color:#f8fafc; padding:16px;">
          <pre style="font-family:monospace; font-size:12px; line-height:1.5; overflow:auto; max-height:480px; margin:0;">${JSON.stringify(row, null, 2)}</pre>
        </div>
        <div class="erp-modal-footer" style="background:#0f172a; border-color:#1e293b;">
          <button class="btn-secondary" onclick="navigator.clipboard.writeText(JSON.stringify(row, null, 2)); alert('JSON 已复制到剪贴板！');">复制 JSON</button>
          <button class="btn-primary" onclick="document.getElementById('dbRowJsonModal').remove()">关闭</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  openSchemaModal() {
    if (!this.cachedTableData) return;
    const { table_name, display_name, columns } = this.cachedTableData;

    const overlay = document.createElement("div");
    overlay.className = "erp-modal-overlay";
    overlay.id = "dbSchemaModal";
    overlay.innerHTML = `
      <div class="erp-modal-container large" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <div>
            <h3>📋 数据表字段架构与约束规范 (Schema Definition)</h3>
            <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">表名: <code>${table_name}</code> (${display_name})</p>
          </div>
          <button class="erp-modal-close-btn" onclick="document.getElementById('dbSchemaModal').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <table class="data-table">
            <thead>
              <tr>
                <th>列名 (Column Name)</th>
                <th>SQL 数据类型</th>
                <th>约束特性</th>
                <th>允许 NULL</th>
              </tr>
            </thead>
            <tbody>
              ${columns.map(c => `
                <tr>
                  <td><code>${c.name}</code></td>
                  <td><strong>${c.type}</strong></td>
                  <td>${c.primary_key ? '<span class="badge badge-warning">🔑 主键 (PRIMARY KEY)</span>' : '<span style="color:var(--text-muted);">常规属性</span>'}</td>
                  <td>${c.nullable ? '<span style="color:var(--text-muted);">YES</span>' : '<span class="badge badge-info">NOT NULL</span>'}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="erp-modal-footer">
          <button class="btn-secondary" onclick="document.getElementById('dbSchemaModal').remove()">关闭</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  exportCurrentTableCsv() {
    if (!this.cachedTableData || !this.cachedTableData.rows.length) {
      alert("当前无数据可导出！");
      return;
    }
    const { table_name, columns, rows } = this.cachedTableData;
    const headers = columns.map(c => c.name);
    
    let csvContent = "\uFEFF"; // UTF-8 BOM 避免 Excel 乱码
    csvContent += headers.map(h => `"${h}"`).join(",") + "\r\n";

    rows.forEach(r => {
      const line = headers.map(h => {
        let val = r[h];
        if (val === null || val === undefined) val = "";
        val = String(val).replace(/"/g, '""');
        return `"${val}"`;
      }).join(",");
      csvContent += line + "\r\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${table_name}_export_${new Date().toISOString().substring(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  // =========================================================================
  // 💾 2. 数据库事务快照与安全回滚 (Backup & Rollback)
  // =========================================================================
  async renderBackupsView(container) {
    container.innerHTML = `
      <!-- 系统健康状态条 -->
      <div class="content-card" style="margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>系统运行健康度 (Health Probe):</strong>
            <span id="sysHealthStatus" class="badge badge-success" style="margin-left:8px;">OPERATIONAL</span>
            <span id="sysUptime" style="font-size:12px; color:var(--text-muted); margin-left:12px;">--</span>
          </div>
          <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.refreshHealth()">🔄 刷新状态</button>
        </div>
      </div>

      <!-- 数据库备份与一致性校验 -->
      <div class="content-card">
        <div class="card-header-bar" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
          <h3>💾 数据库事务快照与防篡改记录 (docs/05)</h3>
          <span class="badge badge-info">PostgreSQL 16 / SQLite ACID</span>
        </div>
        <div id="backupListContainer" class="table-container">正在加载快照列表...</div>
      </div>
    `;

    await this.refreshHealth();
    await this.refreshBackups();
  },

  async refreshHealth() {
    try {
      const h = await ApiClient.get("/system/health");
      const el = document.getElementById("sysHealthStatus");
      if (el) el.textContent = h.status.toUpperCase();
      const up = document.getElementById("sysUptime");
      if (up) up.textContent = `运行时间: ${h.uptime_seconds}s · 环境: ${h.environment}`;
    } catch (e) {
      console.error(e);
    }
  },

  async refreshBackups() {
    const box = document.getElementById("backupListContainer");
    if (!box) return;
    try {
      const list = await ApiClient.get("/system/backups");
      box.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>快照文件名</th>
              <th>类型</th>
              <th>大小</th>
              <th>SHA-256 完整性防篡改哈希</th>
              <th>建立时间</th>
              <th>一致性核验</th>
            </tr>
          </thead>
          <tbody>
            ${list.map(b => `
              <tr>
                <td><code>${b.backup_name}</code></td>
                <td><span class="badge badge-info">${b.backup_type}</span></td>
                <td>${(b.file_size_bytes / 1024).toFixed(1)} KB</td>
                <td><code style="font-size:11px;">${b.sha256_checksum.substring(0, 24)}...</code></td>
                <td>${b.created_at.substring(0, 19).replace('T', ' ')}</td>
                <td>
                  <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.verifyBackup('${b.id}')">校验防篡改</button>
                </td>
              </tr>
            `).join("") || '<tr><td colspan="6">暂无快照</td></tr>'}
          </tbody>
        </table>
      `;
    } catch (err) {
      box.innerHTML = `<div class="auth-alert error">加载备份记录失败: ${err.message}</div>`;
    }
  },

  async triggerManualSnapshot() {
    try {
      const snap = await ApiClient.post("/system/backups/snapshot", { notes: "管理员控制台一键一致性快照" });
      alert(`🎉 快照建立成功！\n文件名: ${snap.backup_name}\nSHA-256: ${snap.sha256_checksum}`);
      if (this.currentSub === "backup") await this.refreshBackups();
    } catch (err) {
      alert("快照失败: " + err.message);
    }
  },

  async verifyBackup(id) {
    try {
      const res = await ApiClient.get(`/system/backups/${id}/verify`);
      alert(`防篡改校验报告：\n快照: ${res.backup_name}\n哈希匹配: ${res.is_tamper_free ? '✓ 完美匹配 (未被篡改)' : '✕ 异常'}\n安全回滚评估: ${res.can_safely_rollback ? '✓ 安全' : '✕ 风险'}`);
    } catch (err) {
      alert("校验失败: " + err.message);
    }
  },

  // =========================================================================
  // 📡 3. 开发者实时系统日志流 (Logs Stream)
  // =========================================================================
  async renderLogsView(container) {
    container.innerHTML = `
      <div class="content-card" style="background:#0f172a; color:#f8fafc; border-color:#1e293b;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#10b981;"></span>
            <strong style="color:#38bdf8;">实时日志捕获流 (Live Log Stream)</strong>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn-secondary btn-xs" style="background:#1e293b; color:#fff; border-color:#334155;" onclick="window.DepartmentSystem.triggerTestLog()">+ 触发测试日志</button>
            <button class="btn-secondary btn-xs" style="background:#1e293b; color:#fff; border-color:#334155;" onclick="window.DepartmentSystem.refreshLogs()">🔄 刷新日志</button>
          </div>
        </div>
        <div id="liveLogsTerminal" style="font-family:monospace; font-size:12px; max-height:480px; overflow-y:auto; line-height:1.6; padding:12px; background:#020617; border-radius:6px;">
          正在捕获实时日志流...
        </div>
      </div>
    `;

    await this.refreshLogs();
  },

  async refreshLogs() {
    const term = document.getElementById("liveLogsTerminal");
    if (!term) return;
    try {
      const res = await ApiClient.get("/system/logs?limit=40");
      term.innerHTML = res.logs.map(l => `
        <div style="padding:2px 0;">
          <span style="color:#64748b;">[${l.timestamp.substring(11, 19)}]</span>
          <span style="color:${l.level === 'ERROR' ? '#f87171' : (l.level === 'WARNING' ? '#fbbf24' : '#38bdf8')}; font-weight:700;">[${l.level}]</span>
          <span style="color:#e2e8f0;">${l.message}</span>
        </div>
      `).join("") || "暂无日志";
      term.scrollTop = term.scrollHeight;
    } catch (err) {
      term.innerHTML = `<span style="color:#f87171;">无法加载日志: ${err.message}</span>`;
    }
  },

  async triggerTestLog() {
    try {
      await ApiClient.post("/system/logs/test?level=INFO&message=管理员触发实机连通性健康日志");
      await this.refreshLogs();
    } catch (err) {
      alert("触发失败: " + err.message);
    }
  },

  // =========================================================================
  // 📁 4. 全局受控附件与多媒体资产管理 (Attachment Management - docs/15)
  // =========================================================================
  attachmentFilterModel: "",
  attachmentPage: 1,

  async renderAttachmentsView(container) {
    container.innerHTML = `<div class="loading-spinner">正在读取系统受控附件与存储资产...</div>`;
    try {
      const [stats, atts] = await Promise.all([
        ApiClient.get("/system/attachments/stats"),
        ApiClient.get(`/system/attachments?page=${this.attachmentPage}&page_size=25${this.attachmentFilterModel ? `&res_model=${this.attachmentFilterModel}` : ''}`)
      ]);

      container.innerHTML = `
        <!-- 统计指标看板 -->
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px;">
          <div class="content-card" style="padding:14px; text-align:center;">
            <div style="font-size:12px; color:var(--text-muted);">📁 受控附件总数</div>
            <div style="font-size:24px; font-weight:800; color:var(--primary); margin-top:4px;">${stats.total_count} 项</div>
          </div>
          <div class="content-card" style="padding:14px; text-align:center;">
            <div style="font-size:12px; color:var(--text-muted);">💾 磁盘存储占用</div>
            <div style="font-size:24px; font-weight:800; color:#10b981; margin-top:4px;">${stats.total_size_mb} MB</div>
          </div>
          <div class="content-card" style="padding:14px; text-align:center;">
            <div style="font-size:12px; color:var(--text-muted);">👥 HR 员工头像</div>
            <div style="font-size:24px; font-weight:800; color:#8b5cf6; margin-top:4px;">${stats.model_breakdown["hr_employee"] || 0} 张</div>
          </div>
          <div class="content-card" style="padding:14px; text-align:center;">
            <div style="font-size:12px; color:var(--text-muted);">📐 产品物料实物图</div>
            <div style="font-size:24px; font-weight:800; color:#f59e0b; margin-top:4px;">${stats.model_breakdown["product_master"] || 0} 张</div>
          </div>
        </div>

        <!-- 操作与过滤工具条 -->
        <div class="content-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-size:13px; font-weight:700;">业务模型分类:</span>
              <select id="attModelFilter" class="form-select" style="width:170px; padding:4px 8px; font-size:12.5px;" onchange="window.DepartmentSystem.onFilterAttachmentModel(this.value)">
                <option value="" ${this.attachmentFilterModel === '' ? 'selected' : ''}>-- 全部业务领域 --</option>
                <option value="hr_employee" ${this.attachmentFilterModel === 'hr_employee' ? 'selected' : ''}>HR 员工档案头像</option>
                <option value="product_master" ${this.attachmentFilterModel === 'product_master' ? 'selected' : ''}>产品物料实物图</option>
                <option value="dms_document" ${this.attachmentFilterModel === 'dms_document' ? 'selected' : ''}>DMS 受控文件附件</option>
                <option value="system" ${this.attachmentFilterModel === 'system' ? 'selected' : ''}>系统通用附件</option>
              </select>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn-primary btn-xs" onclick="window.DepartmentSystem.openUploadAttachmentModal()">📤 上传新受控附件</button>
              <button class="btn-secondary btn-xs" onclick="window.DepartmentSystem.renderAttachmentsView(document.getElementById('systemSubContent'))">🔄 刷新列表</button>
            </div>
          </div>

          <!-- 附件数据表格 -->
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th style="width:50px; text-align:center;">缩略图</th>
                  <th>原始文件名</th>
                  <th>业务所属模型</th>
                  <th>关联实体 ID</th>
                  <th>文件大小</th>
                  <th>MIME 类型</th>
                  <th>SHA-256 数据一致性校验哈希</th>
                  <th>登记时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                ${atts.items && atts.items.length ? atts.items.map(a => `
                  <tr>
                    <td style="text-align:center;">
                      ${(a.content_type.startsWith('image/') || a.file_name.endsWith('.svg')) ? `
                        <img src="${a.file_url}" style="width:36px; height:36px; object-fit:contain; border-radius:4px; border:1px solid var(--border-color); cursor:pointer; background:#fff;" onclick="window.DepartmentSystem.previewAttachmentLarge('${a.file_url}', '${a.file_name}')">
                      ` : `
                        <span style="font-size:24px;">📄</span>
                      `}
                    </td>
                    <td>
                      <strong>${a.file_name}</strong>
                      <div style="font-size:11px; color:var(--text-muted);">${a.description || ''}</div>
                    </td>
                    <td>
                      <span class="badge ${a.res_model === 'hr_employee' ? 'badge-primary' : (a.res_model === 'product_master' ? 'badge-warning' : 'badge-secondary')}">
                        ${a.res_model}
                      </span>
                    </td>
                    <td><code>${a.res_id ? a.res_id.substring(0, 8) + '...' : '--'}</code></td>
                    <td>${(a.file_size / 1024).toFixed(1)} KB</td>
                    <td><code>${a.content_type}</code></td>
                    <td>
                      <code style="font-size:11px; color:#475569;" title="${a.sha256_hash}">${a.sha256_hash.substring(0, 12)}...</code>
                      <button class="btn-secondary btn-xs" style="padding:1px 4px; font-size:10px; margin-left:4px;" onclick="navigator.clipboard.writeText('${a.sha256_hash}'); alert('✓ SHA256 哈希已复制到剪贴板！')">复制</button>
                    </td>
                    <td><span style="font-size:12px; color:var(--text-muted);">${a.created_at ? a.created_at.substring(0, 19).replace('T', ' ') : '--'}</span></td>
                    <td>
                      <div style="display:flex; gap:6px;">
                        <a href="${a.file_url}" target="_blank" class="btn-secondary btn-xs">查看</a>
                        <button class="btn-danger btn-xs" onclick="window.DepartmentSystem.deleteAttachment('${a.id}', '${a.file_name}')">删除</button>
                      </div>
                    </td>
                  </tr>
                `).join("") : '<tr><td colspan="9" style="text-align:center; padding:24px; color:var(--text-muted);">暂无符合条件的附件数据</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="auth-alert error">加载附件失败: ${err.message}</div>`;
    }
  },

  onFilterAttachmentModel(val) {
    this.attachmentFilterModel = val;
    this.attachmentPage = 1;
    this.renderAttachmentsView(document.getElementById("systemSubContent"));
  },

  previewAttachmentLarge(url, filename) {
    const existing = document.getElementById("attPreviewModalOverlay");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "attPreviewModalOverlay";
    overlay.className = "erp-modal-overlay";
    overlay.style.zIndex = "1100";
    overlay.innerHTML = `
      <div class="erp-modal-container medium" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>🖼️ 附件高分辨率预览: ${filename}</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('attPreviewModalOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body" style="text-align:center; background:#0f172a; padding:24px; border-radius:6px;">
          <img src="${url}" style="max-width:100%; max-height:450px; object-fit:contain; box-shadow:0 8px 24px rgba(0,0,0,0.4);">
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  openUploadAttachmentModal() {
    const existing = document.getElementById("attUploadModalOverlay");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "attUploadModalOverlay";
    overlay.className = "erp-modal-overlay";
    overlay.style.zIndex = "1050";
    overlay.innerHTML = `
      <div class="erp-modal-container small" onclick="event.stopPropagation()">
        <div class="erp-modal-header">
          <h3>📤 上传新受控附件 (ISO 9001 / DMS)</h3>
          <button class="erp-modal-close-btn" onclick="document.getElementById('attUploadModalOverlay').remove()">✕</button>
        </div>
        <div class="erp-modal-body">
          <form id="sysUploadAttForm" onsubmit="event.preventDefault(); window.DepartmentSystem.submitUploadAttachment();">
            <div class="form-group" style="margin-bottom:12px;">
              <label class="form-label">选择本地文件 *</label>
              <input type="file" id="suFile" class="form-input" required>
            </div>
            <div class="form-group" style="margin-bottom:12px;">
              <label class="form-label">所属业务模型 (res_model) *</label>
              <select id="suModel" class="form-select" required>
                <option value="system">system (系统通用)</option>
                <option value="hr_employee">hr_employee (HR员工档案)</option>
                <option value="product_master">product_master (产品主数据)</option>
                <option value="dms_document">dms_document (受控体系文档)</option>
              </select>
            </div>
            <div class="form-group" style="margin-bottom:12px;">
              <label class="form-label">关联业务实体 ID (可选)</label>
              <input type="text" id="suResId" class="form-input" placeholder="输入关联的 UUID，如员工ID或产品ID">
            </div>
            <div class="form-group" style="margin-bottom:12px;">
              <label class="form-label">附件说明备注</label>
              <input type="text" id="suDesc" class="form-input" placeholder="简要说明此附件内容">
            </div>
            <div style="margin-top:16px; display:flex; justify-content:flex-end; gap:8px;">
              <button type="button" class="btn-secondary" onclick="document.getElementById('attUploadModalOverlay').remove()">取消</button>
              <button type="submit" id="suSubmitBtn" class="btn-primary">✓ 确认上传并计算哈希</button>
            </div>
          </form>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  },

  async submitUploadAttachment() {
    const fileInput = document.getElementById("suFile");
    if (!fileInput.files || !fileInput.files[0]) {
      alert("请选择要上传的文件！");
      return;
    }
    const btn = document.getElementById("suSubmitBtn");
    btn.disabled = true;
    btn.textContent = "正在计算哈希并上传...";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("res_model", document.getElementById("suModel").value);
    const resId = document.getElementById("suResId").value.trim();
    if (resId) formData.append("res_id", resId);
    const desc = document.getElementById("suDesc").value.trim();
    if (desc) formData.append("description", desc);

    try {
      await ApiClient.uploadFormData("/system/attachments/upload", formData);
      alert("✓ 附件上传成功并已登记至受控资产库！");
      const m = document.getElementById("attUploadModalOverlay");
      if (m) m.remove();
      await this.renderAttachmentsView(document.getElementById("systemSubContent"));
    } catch (err) {
      alert("上传失败: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✓ 确认上传并计算哈希";
      }
    }
  },

  async deleteAttachment(attId, filename) {
    if (!confirm(`确定要移除受控附件 "${filename}" 吗？此操作将软删除该元数据记录。`)) return;
    try {
      await ApiClient.delete(`/system/attachments/${attId}`);
      alert("✓ 附件已安全移除！");
      await this.renderAttachmentsView(document.getElementById("systemSubContent"));
    } catch (err) {
      alert("删除失败: " + err.message);
    }
  }
};
