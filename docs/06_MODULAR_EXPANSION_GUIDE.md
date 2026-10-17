# 06 - 业务功能模块平滑扩展规范 (Modular Expansion Guide)

---

## 1. 扩展理念与解耦设计

用户的核心规划：  
> **“其他功能模块我在稍后的对话中逐渐给你完善。”**

为避免系统在增加新模块（如后续的：生产管理、仓储物流、供应商管理、KBA 型式认证专门审验模块）时演变成代码混乱的“大泥球”，Bravio ERP 采用 **领域驱动设计（DDD）思想的模块化单体（Modular Monolith）** 架构。

每一个模块均是一个**高内聚、低耦合、自包含**的独立单元。新增模块如同“插入一个 USB 设备”，即插即用，绝不污染系统全局核心。

---

## 2. 后端新业务模块标准目录契约

在 `backend/app/modules/` 下，任何新增模块均遵循统一的标准契约文件树：

```text
backend/app/modules/[module_name]/
├── __init__.py
├── manifest.py            # 模块元数据 (模块名、版本、图标、依赖的前置模块、菜单配置)
├── models.py              # 数据模型定义 (必须继承 BaseAuditModel，自带合规审计能力)
├── schemas.py             # 数据校验契约 (Pydantic v2 请求与响应模型)
├── service.py             # 核心领域业务逻辑 (事务、规则计算、状态机)
├── router.py              # API 路由端点 (FastAPI 路由组，自动集成 OpenAPI)
├── permissions.py         # 该模块声明的 RBAC 权限代码集
└── events.py              # 模块对内对外发布的领域事件 (基于事件解耦)
```

### 2.1 模块自注册与即插即用机制 (`manifest.py`)
每个模块通过 `manifest.py` 向系统声明自身：
```python
# 示例：未来扩展的 KBA 型式认证跟踪模块 manifest.py
MODULE_MANIFEST = {
    "name": "kba_homologation",
    "display_name": "KBA 型式认证与生产一致性 (CoP)",
    "version": "1.0.0",
    "icon": "shield-check",        # Odoo App Switcher 九宫格展示的图标
    "category": "Quality & Compliance",
    "depends": ["system_auth", "rbac", "hr_employees"], # 依赖模块
    "sequence": 20,                # 在九宫格菜单中的排序权重
    "permissions": [
        ("kba.cop.view", "查看 KBA CoP 档案与试验记录"),
        ("kba.cop.manage", "编辑与维护型式认证参数"),
        ("kba.cop.approve", "签发生产一致性合规报告 (需2FA)")
    ]
}
```
系统启动时，路由装载器会自动扫描所有子目录中的 `manifest.py`，并将路由与权限自动注册至全局网关，无需手动侵入修改全局文件。

---

## 3. 前端新模块标准规范

前端新增视图时，100% 复用统一打造的 Odoo 基础组件库，开发效率极高，且保持全系统体验统一：

```text
frontend/src/views/[module_name]/
├── index.vue              # 模块入口页 (通常为 List 列表视图)
├── components/            # 模块专有子组件
│   ├── [Module]Form.vue   # Form 表单详情页 (内嵌 Status Pipeline 与 Chatter)
│   └── [Module]Kanban.vue # 看板视图 (如任务流转、状态推进)
└── api.ts                 # 该模块所有 HTTP 请求封装 (TypeScript 类型约束)
```

### 3.1 前端页面标准三步极简开发法
1. **第一步（引用 ControlPanel）**：直接使用全局统一的搜索条、过滤器和分组器。
2. **第二步（选择展示视图）**：根据需要装载 `ListView` 或 `KanbanView`。
3. **第三步（挂载 Chatter）**：在详情页右侧或底部插入 `<Chatter :record-id="id" :model-name="module_name" />`，该模块即刻拥有完整的沟通、待办与审计追踪能力。

---

## 4. 跨模块通信准则：事件总线（Event Bus）

严禁直接跨模块写死复杂的跨库联表查询或硬调用。跨模块协同统一采用异步事件解耦：
- 例如：当“质检模块”发现某工位生产异常时，质检模块只需发出领域事件 `QualityDeviationOccurred`。
- “人员管理模块”监听到该事件后，自动核查操作该工位员工的资质是否需要复核；“通知模块”自动给质量总监发送邮件。
- 模块间彼此完全解耦，随时可拆分、可插拔。
