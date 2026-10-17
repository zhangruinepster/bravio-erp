# Vibe Coding 连续开发与协同守则 (Vibe Coding Guidelines)

---

## 1. 为什么需要 Vibe Coding 守则？

“Vibe Coding”（氛围式敏捷开发）倡导人机协同、自然语言驱动、快速原型与流畅的迭代心流。  
但在企业级复杂系统（尤其是涉及 **ISO 9001** 与 **KBA 严格合规** 的 ERP）中，随着对话轮次增加或开启新会话，极易发生“上下文丢失”、“架构偏离约定”、“AI 产生幻觉重构底层”等问题。

本守则作为人机协同的**“记忆定海神针”**，确保后续无论在何时何地开启对话，任何 AI 助手都能在 1 秒内无缝对齐项目的核心理念与架构规范。

---

## 2. 核心工作流协议 (Session Protocol)

### 2.1 每次新会话启动守则 (Session Bootstrap)
当用户或开发者在新对话中提出：“我们来继续做 Bravio ERP 的 XX 模块”时，AI 助手必须首先执行以下步骤：
1. **优先读取项目索引**：查阅根目录 [README.md](file:///c:/Users/zhang/Documents/Python/bravio-erp/README.md) 与 `docs/` 目录。
2. **校验核心边界**：
   - 绝不引入 Odoo 原版框架/ORM 代码（UI 交互复刻 Odoo，但代码底座自主研发）。
   - 所有的业务模型必须继承 `BaseAuditModel`（自带创建、修改、软删除与版本乐观锁）。
   - 涉及数据修改与删除的操作，必须预留审计流水（Audit Trail）捕获钩子。
   - 数据库必须考虑事务完整性与一致性。
3. **查阅对应规范文件**：
   - 做界面交互时查阅 [02_UI_UX_ODOO_SPECIFICATION.md](file:///c:/Users/zhang/Documents/Python/bravio-erp/docs/02_UI_UX_ODOO_SPECIFICATION.md)。
   - 做权限时查阅 [03_SECURITY_AND_RBAC.md](file:///c:/Users/zhang/Documents/Python/bravio-erp/docs/03_SECURITY_AND_RBAC.md)。
   - 做新业务扩展时查阅 [06_MODULAR_EXPANSION_GUIDE.md](file:///c:/Users/zhang/Documents/Python/bravio-erp/docs/06_MODULAR_EXPANSION_GUIDE.md)。

---

## 3. 文档先行与同步更新准则 (Doc-Code Sync)

1. **逻辑先于代码**：在编写具体代码前，先在对应模块内理清字段、状态机、权限点和主要 API。
2. **变更同步留痕**：如果开发过程中对表结构进行了重大调整，或者增加了新的业务状态，必须同步更新 `docs/` 中对应的说明文档。
3. **架构决策记录 (ADR)**：若发生关键技术选型变更（如改变缓存方案、升级认证算法），应在 `docs/` 中记录简明 ADR 条目（背景、决策、后果）。

---

## 4. Git 版本管理与提交规范 (Git Commit Standards)

整个代码仓库推送到 GitHub 时，应遵循清晰的语义化提交信息（Conventional Commits），方便回溯与自动生成变更日志（Changelog）：

| 前缀 | 适用场景 | 示例 |
| :--- | :--- | :--- |
| **`feat`** | 新增业务功能或组件 | `feat(hr): 增加员工 KBA 资质矩阵到期预警功能` |
| **`fix`** | 修复 Bug 或逻辑缺陷 | `fix(auth): 修复双因子验证备用码散列核验问题` |
| **`docs`** | 文档更新与逻辑规范修订 | `docs: 完善 05 号灾备回滚规范的 SHA256 流程图` |
| **`refactor`**| 重构代码（无新功能也无功能修复）| `refactor(odoo-ui): 优化 ControlPanel 胶囊过滤组件性能` |
| **`test`** | 增加或修改单元测试/集成测试 | `test(audit): 补充修改员工状态时写入审计日志的断言` |
| **`chore`**| 基础设施、依赖包或 Docker 配置变动 | `chore(docker): 更新 PostgreSQL 16 镜像及 WAL 刷盘参数` |

---

## 5. 编码不可突破的“红线” (Non-negotiable Guardrails)

- 🚫 **红线 1：禁止使用硬删除（Hard Delete）**。生产与业务表必须使用 `is_deleted` 软删除，合规审计记录必须终身保留。
- 🚫 **红线 2：禁止任何裸 SQL 拼接**。必须使用参数化查询或 ORM 安全绑定，杜绝 SQL 注入。
- 🚫 **红线 3：禁止敏感数据明文传输与存储**。密码、Token 密钥严禁明文存盘，严禁将生产数据库账号写死在代码中。
- 🚫 **红线 4：禁止破坏事务原子性**。涉及主子表关联或审计记录写入的多步骤更新，必须包裹在同一个受保护的事务内。
