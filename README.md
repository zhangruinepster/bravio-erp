# Bravio ERP 系统

> **企业定位**：持有 ISO 9001 质量管理体系认证、面向德国联邦机动车运输管理局（KBA）Type Approval（型式认证与生产一致性 CoP）合规要求的高可靠企业级 ERP 平台。  
> **设计哲学**：深度融合 **Odoo 现代化交互体验** 与 **轻量高可靠自研工程架构**（完全重构底层数据库、业务模型与模块扩展机制）。

---

## 📌 项目核心诉求与关键特性

1. **Odoo 交互风格 + 现代自主技术底座**
   - 顶部应用切换九宫格（App Switcher）、面包屑路径导航。
   - 强悍的统一控制台（Control Panel）：智能搜索、多维过滤（Filters）、多层分组（Group By）、快捷收藏（Favorites）。
   - 标准多视图：列表视图（List）、表单视图（Form，含状态流水线与智能按钮）、看板视图（Kanban）。
   - 核心审计跟踪侧边栏（Chatter）：沟通消息、内部备注、日程待办、底层字段级自动审计流水（Audit Trail）。
2. **工业级 32 位激光码与四级包装聚合溯源（Traceability & WMS Core）**
   - 32 位 DataMatrix 激光码（零件号、版本、周次、流水号、LED Binning 档位）由数据库原生 `STORED` 计算列直接物化。
   - 包装工位双灯强制配对防呆（Poka-Yoke）：色温/光通量/电压 Binning 100% 强比对，全屏声光拦截。
   - `SN -> BOX -> CARTON -> PALLET` 四级树状聚合，`WITH RECURSIVE` 递归穿透毫秒级出入库与状态调拨。
   - 德国仓 IQC 抽检解构（余箱 `PARTIAL` 降级、彩盒解绑、慕尼黑实验室留样与售后散件备用池 `LOOSE_SPARE`）。
   - 售后 RMA 逆向风控：换盒欺诈拦截、跨区串货核验、同批次留样物理货架秒级定位、同 Binning 备件精准补发。
3. **严苛的合规体系支持（ISO 9001 & KBA CoP）**
   - 不可篡改的数据变更轨迹（记录修改前/后值、操作人、IP、时间戳、审批依据）。
   - 人员能力与合规资质矩阵（资质到期预警、技能上岗认证）。
   - 变更管理（Management of Change）与流程签批闭环。
4. **企业级安全防护与权限体系（RBAC & ABAC）**
   - 密码哈希采用业界公认最坚固的 Argon2id。
   - 强制/可选多因子认证（MFA / TOTP）。
   - 细粒度权限控制：菜单权限、按钮/操作级权限、行级/组织级数据隔离（Row-Level Security）。
5. **零数据丢失保障与灾备回滚系统**
   - 纯标准 PostgreSQL 16 ACID 强事务与预写日志（WAL）。
   - 容器化定时快照与自动备份守护进程（带 SHA256 校验与版本归档）。
   - 管理员独立文件一键导出与安全事务级回滚（恢复前自动创建保护快照）。
6. **持续长效的 Vibe Coding 开发体验**
   - 详尽的文档矩阵驱动，业务逻辑与组件规范先于代码固化，确保 AI 辅助开发在跨对话周期中始终保持上下文连续性。

---

## 📚 项目逻辑与组件规格文档库 (`docs/`)

为确保整个项目的业务逻辑、组件交互与架构设计清晰透明，所有逻辑已按专业规范固化在 `docs/` 目录中：

| 序号 | 文档名称 | 核心内容概览 |
| :---: | :--- | :--- |
| **00** | [00_PROJECT_OVERVIEW.md](docs/00_PROJECT_OVERVIEW.md) | 企业背景、ISO9001/KBA合规技术指标、系统定位与非功能性要求 |
| **01** | [01_ARCHITECTURE_AND_EXECUTION.md](docs/01_ARCHITECTURE_AND_EXECUTION.md) | 总体架构、服务组件、请求生命周期与程序执行结构全景 |
| **02** | [02_UI_UX_ODOO_SPECIFICATION.md](docs/02_UI_UX_ODOO_SPECIFICATION.md) | Odoo 风格组件交互规范（ControlPanel, ListView, FormView, Chatter 等） |
| **03** | [03_SECURITY_AND_RBAC.md](docs/03_SECURITY_AND_RBAC.md) | 企业级安全、认证中心、双因子MFA、RBAC+ABAC权限与审计模型 |
| **04** | [04_PERSONNEL_MANAGEMENT_SPEC.md](docs/04_PERSONNEL_MANAGEMENT_SPEC.md) | 人员、部门、岗位、员工档案与 ISO/KBA 资质证书矩阵逻辑 |
| **05** | [05_DATABASE_CONSISTENCY_AND_BACKUP.md](docs/05_DATABASE_CONSISTENCY_AND_BACKUP.md) | 数据库一致性、定时备份、管理员单文件导出与安全回滚机制 |
| **06** | [06_MODULAR_EXPANSION_GUIDE.md](docs/06_MODULAR_EXPANSION_GUIDE.md) | 模块化单体扩展规范、领域驱动（DDD）与后续业务模块接入指南 |
| **07** | [07_TRACEABILITY_AND_SN_SPECIFICATION.md](docs/07_TRACEABILITY_AND_SN_SPECIFICATION.md) | **32位激光微距码切片**、PostgreSQL STORED 计算列、一盒双支 Binning 防呆状态机与工位声光反馈 |
| **08** | [08_PACKAGING_TREE_AND_WMS_LIFECYCLE.md](docs/08_PACKAGING_TREE_AND_WMS_LIFECYCLE.md) | **四级包装聚合树 (SN->BOX->CTN->PLT)**、WITH RECURSIVE 递归穿透、德国仓 IQC 抽检拆解与留样散件池 |
| **09** | [09_RMA_REVERSE_RISK_CONTROL_AND_AUDIT.md](docs/09_RMA_REVERSE_RISK_CONTROL_AND_AUDIT.md) | **售后 RMA 逆向风控**：换盒欺诈拦截、跨区串货预警、孪生件状态关联、慕尼黑实验室留样秒级定位与同Bin散件精准补发 |
| **10** | [10_PRODUCT_MANAGEMENT_AND_LIFECYCLE.md](docs/10_PRODUCT_MANAGEMENT_AND_LIFECYCLE.md) | **产品主数据与 APQP 阶段门生命周期**：料号唯一性、认证属性、APQP 六大阶段门管控、供应商报告上传与 OEM 验收流 |
| **11** | [11_LEAN_BOM_AND_PACKAGING_HIERARCHY.md](docs/11_LEAN_BOM_AND_PACKAGING_HIERARCHY.md) | **轻量级 BOM 与出货包装层级**：总成/零件/说明书/包材四大分类、彩盒/外箱/托盘三级出运态、BOM 版本排他生效与自动归档 |
| **12** | [12_CONFIGURABLE_BARCODE_RULES_ENGINE.md](docs/12_CONFIGURABLE_BARCODE_RULES_ENGINE.md) | **多层级可配置条码规则引擎**：SN/BOX/CTN/PLT 四级默认编码模板、动态占位符标记字典、全链路无损逆向解析兼容保障 |
| **13** | [13_ENGINEERING_CHANGE_MANAGEMENT.md](docs/13_ENGINEERING_CHANGE_MANAGEMENT.md) | **汽车级工程设计变更管理 (PLM 标准)**：ECR/ECO/ECN 闭环、图纸/BOM/测试数据/KBA评价四大证据包上传、发布与永久锁定 |
| **14** | [14_QMS_INSPECTION_AND_INCIDENT_8D.md](docs/14_QMS_INSPECTION_AND_INCIDENT_8D.md) | **质量管理、全流程质检与 8D 失效管理**：制造端出厂 FQC、德国仓入库 IQC、产品级全局质量驾驶舱台账、Bravio 失效 8D 闭环与免整改归档 |
| **15** | [15_GLOBAL_CONTROLLED_WIKI_AND_DMS.md](docs/15_GLOBAL_CONTROLLED_WIKI_AND_DMS.md) | **全局受控知识库与文档管理系统 (DMS)**：ISO 9001 四层金字塔成文信息、细粒度组织与供应商权限隔离、受控版本发布与动态防泄密半透明水印 |
| **16** | [16_EXTERNAL_B2B_API_SPECIFICATION.md](docs/16_EXTERNAL_B2B_API_SPECIFICATION.md) | **外部制造商与物流仓储标准 API 规范**：M2M Token 与 IP 白名单、工单/条码预分配、自定义检测项出厂 FQC 上传、仓库 IQC 调阅与临出库地址变更 |
| **17** | [17_SUPPLIER_AND_CUSTOMER_MANAGEMENT.md](docs/17_SUPPLIER_AND_CUSTOMER_MANAGEMENT.md) | **供应商与客户管理模块 (Odoo 风格)**：商业伙伴通用模型、供应商代工资质与 API 密钥绑定、客户多送货网点管理与 B2B 质保账期条款 |
| **审计**| [ERP_SYSTEM_PRE_CONSTRUCTION_AUDIT_REPORT.md](audit/ERP_SYSTEM_PRE_CONSTRUCTION_AUDIT_REPORT.md) | **建前架构与数据审计总报告**：补全缺失核心实体、组件盲区与异常场景工作流 |
| **规范**| [VIBE_CODING_GUIDELINES.md](docs/VIBE_CODING_GUIDELINES.md) | 面向开发人员与 AI 的协同开发守则、上下文连续性保障机制 |

---


## 🛠️ 推荐技术选型

- **后端核心**：Python 3.11+ / FastAPI / SQLAlchemy 2.0 (Async) / Pydantic v2 / Alembic
- **前端核心**：Vue 3 (Composition API) / Vite / TypeScript / Pinia / Tailwind CSS + 自研 Odoo 风格组件
- **数据库**：PostgreSQL 16
- **缓存与任务队列**：Redis (用于 Session、Rate Limit 与后台异步任务)
- **部署环境**：Docker / Docker Compose / Nginx 反向代理
