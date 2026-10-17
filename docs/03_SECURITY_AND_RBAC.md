# 03 - 企业级安全防护与权限体系规范 (Security & RBAC/ABAC)

---

## 1. 企业级安全防护基准 (Security Baseline)

为满足 Bravio 进军国际市场及通过 KBA 严苛审查的要求，系统遵循 **纵深防御（Defense-in-Depth）** 与 **零信任（Zero Trust）** 理念构建安全中枢。

### 1.1 身份认证与密码学标准
- **密码哈希散列**：采用当前密码学界推荐的 **Argon2id** 算法（默认内存占用 64MB，迭代 3 轮，并发度 4），彻底防御 GPU/ASIC 离线彩虹表暴力破解。
- **登录防爆破与防撞库**：
  - 基于 Redis 实现 IP 与用户维度的滑动时间窗口计数器。
  - 连续 5 次密码错误自动冻结账号 15 分钟，并触发邮件警报与不可篡改安全事件记录。
- **多因子认证 (MFA / 2FA)**：
  - 原生集成基于时间戳的动态口令协议 **TOTP (RFC 6238)**，兼容 Google Authenticator、Microsoft Authenticator 等主流身份验证器。
  - 超级管理员、质量合规总监、财务及数据备份管理员强制开启 2FA；普通员工可自选开启。
  - 提供 10 组高熵单次备用恢复码（Recovery Codes），以散列形式加密存盘。
- **令牌与会话生命周期**：
  - **Access Token**：高安全性短周期 JWT（有效期 15 分钟），携带最小必要声明。
  - **Refresh Token**：长周期（7 天），存放在严苛设置的 `HttpOnly`, `SameSite=Strict`, `Secure` Cookie 中。
  - **Token 轮换与防重放检测 (Token Rotation)**：每次刷新令牌时旧令牌作废，若检测到旧 Refresh Token 被恶意重放，系统立即将该用户全部有效会话直接吊销。

---

## 2. 混合型访问控制模型（RBAC + ABAC + 数据范围）

传统 RBAC 只能控制“谁能访问什么菜单/按钮”，而在 ISO 9001 和 KBA 的实际业务中，必须能够精准控制“在什么条件下、能操作哪个部门/厂区的哪些数据”。因此 Bravio ERP 采用 **角色基（RBAC）+ 属性基（ABAC）+ 组织数据范围（Data Scope）** 的三合一立体授权体系。

```
                    ┌───────────────────────────────────────────────┐
                    │            用户 (Authenticated User)           │
                    └───────────────────────┬───────────────────────┘
                                            │ 关联
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │               角色 (Assigned Roles)           │
                    │  (如: 质量总监, KBA专员, 研发主管, 外部审核员)│
                    └───────────────────────┬───────────────────────┘
                                            │ 赋予
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
    ┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
    │       功能权限 (Functional Perms)      │   │       数据范围权限 (Data Scopes)      │
    │ 命名空间: module.resource.action      │   │ 控制用户能“看/改”哪一部分记录         │
    │ 例:                                   │   │                                       │
    │ - hr.employee.create                  │   │ 1. ALL (全集团所有数据)               │
    │ - hr.employee.export                  │   │ 2. DEPT_AND_CHILD (所属部门及下属部门)│
    │ - kba.type_approval.approve           │   │ 3. DEPT_ONLY (仅限本直属部门)         │
    │ - system.backup.download              │   │ 4. SELF_ONLY (仅限自己创建/绑定的记录)│
    └───────────────────────────────────────┘   └───────────────────────────────────────┘
```

### 2.1 典型开箱即用角色矩阵（Pre-configured Roles）

| 角色代码 | 角色名称 | 核心职能定位 | 数据范围默认值 |
| :--- | :--- | :--- | :--- |
| **`ROLE_SUPER_ADMIN`** | 超级系统管理员 | 系统配置、灾备管理、用户授权总控 | 全集团 (ALL) |
| **`ROLE_QUALITY_HEAD`** | 质量与合规总监 | ISO 9001 总负责人、KBA 认证最终签批人 | 全集团 (ALL) |
| **`ROLE_KBA_SPECIALIST`**| KBA 生产一致性专员 | 负责型式认证档案、试验记录、CoP 变更评估 | 全集团质量与生产域 |
| **`ROLE_DEPT_MANAGER`** | 部门负责人 | 审批本部门人事调配、考勤、普通业务审批 | 所在部门及下级 (DEPT_AND_CHILD) |
| **`ROLE_ENGINEER`** | 业务执行工程师 | 录入日常技术数据、发起资质申请 | 仅本人及协同单据 (SELF_ONLY) |
| **`ROLE_AUDITOR`** | 外部/内部审核员 | ISO/KBA 审核期间开放，仅允许只读调阅和导出证据 | 全集团受审范围 (只读) |

### 2.2 字段级权限与敏感数据脱敏 (Field-Level Security)
针对关键隐私信息（例如：员工身份证号、个人薪酬、系统核心配置私钥）：
- 数据库底层统一加密或脱敏返回（例如：`310115********1234`）。
- 仅拥有特权权限代码（如 `hr.employee.view_sensitive`）的用户，在调用解密接口时方可查阅明文，且明文查看行为计入安全审计日志。

---

## 3. 不可篡改的数据审计中枢 (Immutable Audit Engine)

满足 ISO 9001（第 7.5 条“成文信息”）及 KBA（生产一致性要求）的关键技术实现：

### 3.1 审计日志模型实体定义 (`audit_trail_logs`)

```sql
CREATE TABLE audit_trail_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    
    -- 操作主体信息
    actor_id UUID NULL REFERENCES sys_users(id),
    actor_username VARCHAR(64) NOT NULL,
    actor_ip VARCHAR(45) NOT NULL,
    actor_user_agent TEXT NOT NULL,
    request_id VARCHAR(64) NOT NULL,
    
    -- 操作客体信息
    target_module VARCHAR(64) NOT NULL,      -- 例: 'hr_employees', 'kba_cop'
    target_table VARCHAR(64) NOT NULL,       -- 例: 'hr_employee_certifications'
    target_id VARCHAR(64) NOT NULL,          -- 目标记录主键
    action_type VARCHAR(32) NOT NULL,        -- 'CREATE', 'UPDATE', 'SOFT_DELETE', 'APPROVE', 'DOWNLOAD'
    
    -- 核心证据：变更前后差异对照 (JSONB 存储)
    changes_diff JSONB NOT NULL,
    
    -- 业务依据与签署理由
    reason TEXT NULL,                         -- 关键审批/变更必须填写的“变更原因”
    is_compliance_critical BOOLEAN DEFAULT FALSE -- 是否属于 KBA/ISO 关键控制项
);

-- 严禁任何用户通过业务系统 UPDATE 或 DELETE 审计日志！
REVOKE UPDATE, DELETE, TRUNCATE ON audit_trail_logs FROM bravio_api_role;
```

### 3.2 变更差异（Diff）捕获实例
当张工的 KBA 资质被审核批准时，`changes_diff` 自动沉淀以下结构：
```json
{
  "fields_changed": ["status", "approver_id", "approved_at"],
  "old_values": {
    "status": "PENDING_AUDIT",
    "approver_id": null,
    "approved_at": null
  },
  "new_values": {
    "status": "APPROVED",
    "approver_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "approved_at": "2026-10-17T10:15:30Z"
  },
  "business_note": "现场实操考核通过，评分98，符合 KBA ECE-RXX 第4章能力规范要求。"
}
```
该数据通过异步机制即时投影至该对象的 **Chatter 时间轴**，在前端界面一目了然呈现给操作人员与审核员。
