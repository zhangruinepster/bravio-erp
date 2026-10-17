# Bravio ERP - 版本演进历史 (Version History)

本项目遵循语义化版本规范（Semantic Versioning, SemVer），记录从基础设施奠基到各业务模块的逐版本迭代历程。每一个版本的发布均经过静态类型检查、自动化测试验证与合规基准审计。

---

## [v0.1.0] - 2026-10-17
### 核心交付：企业组织架构、立体安全RBAC与人员资质合规中枢 (Organizational Structure, RBAC & Personnel Competency)


#### 1. 系统安全与立体权限体系 (Security & RBAC/ABAC - docs/03)
- [x] **数据模型**：设计并建立 `sys_roles`（系统角色）、`sys_permissions`（功能权限）及其关联多对多映射。
- [x] **数据范围控制**：引入 `DataScope` 枚举（`ALL` 全公司、`DEPT_AND_CHILD` 部门及下属、`DEPT_ONLY` 仅本部门、`SELF_ONLY` 仅本人）。
- [x] **权限依赖中枢**：实现基于 FastAPI 依赖注入的细粒度权限校验器（`require_permissions`）与数据范围守卫。
- [x] **内置角色矩阵**：预置 `ROLE_SUPER_ADMIN`、`ROLE_QUALITY_HEAD`、`ROLE_KBA_SPECIALIST`、`ROLE_DEPT_MANAGER` 等 ISO/KBA 合规角色。

#### 2. 人员组织与资质合规管理 (HR & Competency Matrix - docs/04)
- [x] **组织架构树**：建立 `hr_departments`（支持无限级自引用树形结构、ISO 过程类型划分：核心/管理/支持）。
- [x] **岗位体系**：建立 `hr_job_positions`（岗位定义、是否属于关键安全特性工位 `is_safety_critical`、必需证书类型要求）。
- [x] **员工花名册**：建立 `hr_employees`（员工档案、工号生成规则、在职状态生命周期、与系统登录用户解耦绑定）。
- [x] **ISO/KBA 资质矩阵**：建立 `hr_employee_certifications`（证书编号、颁发/到期日期、提前30天到期预警机制、关键工位上岗合规校验）。
- [x] **培训与有效性评价**：建立 `hr_employee_trainings`（记录培训课时、成绩、有效性评价与证书绑定）。

#### 3. 审计流与数据一致性
- [x] 继承通用合规基类 `AuditBase`，实现所有 HR 实体创建、修改、软删除自动留痕并联动审计日志。

#### 4. Odoo 规范交互体系与基于角色的视图隔离 (docs/02 & docs/03)
- [x] **角色视图权限严格隔离**：普通操作员（如车间质检员 `operator`）登录后，自动阻断并隐藏底层系统工作台、数据库监控与开发者实时日志流，仅开放其被授权的业务操作面。
- [x] **Odoo 九宫格应用切换器 (App Switcher)**：顶部导航栏集成 9 点 App Switcher，支持一键在“👥 人力资源与组织架构”、“🏭 车间质检与生产工作台”、“🛠️ 系统运维控制台 (限管理员)”之间无缝切换。
- [x] **统一控制台 (Control Panel)**：实现动态搜索框、快捷过滤胶囊（`在职`、`30天预警`、`特殊工位`）与视图切换器（`列表 List` / `看板 Kanban`）。
- [x] **拟真纸张表单抽屉 (Paper Sheet Drawer)**：
  - 新建员工时支持**一键同步开通 ERP 登录账号与密码**，并分配对应的系统角色与数据范围权限。
  - 支持直接在前端创建/维护组织架构多级部门，以及定义新系统角色与关联功能权限。
- [x] 扩展自动化测试套件：实现 12 项端到端单元与集成测试（包含新员工账号创建及登录认证闭环），通过率 100%。


---

## [v0.0.0] - 2026-10-17
### 初始基座与运行底座奠基 (Foundation & Development Runtime)

#### 1. 架构与工程规范
- 确立 **模块化单体 (Modular Monolith)** 与 **前后端分离** 架构方案。
- 确立依据 **ISO 9001:2015** 质量管理体系与德国 **KBA Type Approval（生产一致性 CoP）** 严苛标准的合规底座。
- 完成 17 份体系设计规范文档（系统架构、安全RBAC、追溯引擎、WMS、BOM、8D客诉、Wiki/DMS等）。

#### 2. 后端核心与持久层
- 基于 Python 3.12 + FastAPI + SQLAlchemy 2.0 异步引擎搭建后端核心服务框架。
- 配置 Docker 容器编排服务（PostgreSQL 16、Redis 7、Backend、Nginx、PgAdmin）。
- 实现不可篡改审计追踪模型 (`audit_logs`) 与安全基础模型 (`AuditBase`)。
- 实现基于 Argon2id 密码散列算法与高安全性 JWT 身份认证体系。

#### 3. 前端与自动化工具
- 基于现代 CSS 与动态交互搭建企业级统一接入控制台（Enterprise Portal）。
- 部署系统健康探针 (`/api/v1/system/health`)、运行时指标与实时日志监控看板。
- 实现一键本地环境启动套件 (`start_dev.bat`)、测试运行器 (`run_tests.bat`) 以及 GitHub 自动化备份与 Tag 推送工具 (`git_push.py`)。
- 完整通过基础身份认证与系统健康自动化测试套件。
