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

#### 4. 前端交互与 API 端点
- [x] 提供完整的 RESTful API 端点：`/api/v1/organization/departments`、`/positions`、`/employees`、`/certifications`。
- [x] 在前端统一控制台（Enterprise Portal）扩展组织架构树与人员资质监控面板。
- [x] 编写完整的自动化单元测试与业务流集成测试，通过率 100%。

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
