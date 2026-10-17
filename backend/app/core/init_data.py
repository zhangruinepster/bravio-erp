from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.logger import logger
from app.models.user import User
from app.models.rbac import Role, Permission, DataScope
from app.models.organization import (
    Department,
    JobPosition,
    Employee,
    EmployeeCertification,
    IsoProcessType,
    EmployeeStatus
)

INITIAL_PERMISSIONS = [
    # 部门与组织权限
    ("hr.department.create", "创建部门", "hr", "创建组织架构树新分支"),
    ("hr.department.read", "查看部门", "hr", "查看组织架构与部门详情"),
    ("hr.department.update", "修改部门", "hr", "修改部门名称与汇报线"),
    ("hr.department.delete", "删除部门", "hr", "删除未绑定的空部门"),
    # 岗位与能力矩阵权限
    ("hr.position.create", "创建岗位", "hr", "新建工位及安全特性资质要求"),
    ("hr.position.read", "查看岗位", "hr", "浏览岗位目录与任职要求"),
    ("hr.position.update", "修改岗位", "hr", "调整工位特殊特性与必需资质"),
    ("hr.position.delete", "删除岗位", "hr", "归档注销岗位"),
    # 员工花名册权限
    ("hr.employee.create", "录入员工", "hr", "录入新入职员工基础信息"),
    ("hr.employee.read", "查看员工", "hr", "查询员工花名册与履历"),
    ("hr.employee.update", "修改员工", "hr", "更新员工档案、调岗及状态"),
    ("hr.employee.delete", "删除员工", "hr", "离职封存或软删除员工档案"),
    # 资质认证与 KBA 审计权限
    ("hr.cert.create", "登记资质证书", "hr", "为员工上报与录入 ISO/KBA 资质"),
    ("hr.cert.read", "查看资质证书", "hr", "检索资质矩阵与到期状态"),
    ("hr.cert.update", "维护资质证书", "hr", "更新证书换证与年审记录"),
    ("kba.cop.audit", "KBA生产一致性审查", "kba", "执行 KBA CoP 工位上岗资格审查与资质阻断"),
    ("kba.type_approval.approve", "型式认证签批", "kba", "签署 Type Approval 核心技术合规文件"),
    # 系统与角色安全权限
    ("system.role.create", "创建系统角色", "rbac", "定义新角色与权限绑定"),
    ("system.role.read", "查看角色权限", "rbac", "查看系统角色矩阵"),
    ("system.backup.manage", "容灾备份管理", "system", "执行与下载数据库快照与归档包"),
]

async def seed_initial_data():
    """初始化预设账号、立体 RBAC 权限与组织架构种子数据 (docs/03 & docs/04)"""
    async with AsyncSessionLocal() as db:
        # =====================================================================
        # 1. 种子化基础权限项 (sys_permissions)
        # =====================================================================
        perm_map = {}
        for code, name, module, desc in INITIAL_PERMISSIONS:
            stmt = select(Permission).where(Permission.code == code)
            perm = (await db.execute(stmt)).scalar_one_or_none()
            if not perm:
                perm = Permission(code=code, name=name, module=module, description=desc)
                db.add(perm)
                await db.flush()
            perm_map[code] = perm

        # =====================================================================
        # 2. 种子化立体角色 (sys_roles)
        # =====================================================================
        # 超级管理员角色
        admin_role_stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code == "ROLE_SUPER_ADMIN")
        admin_role = (await db.execute(admin_role_stmt)).scalar_one_or_none()
        if not admin_role:
            admin_role = Role(
                code="ROLE_SUPER_ADMIN",
                name="超级系统管理员",
                description="拥有系统最高管理权限、全数据范围与容灾控制权",
                data_scope=DataScope.ALL,
                is_system=True,
                permissions=list(perm_map.values())
            )
            db.add(admin_role)
            await db.flush()

        # 质量与合规总监角色 (ISO 9001 / KBA)
        quality_role_stmt = select(Role).where(Role.code == "ROLE_QUALITY_HEAD")
        quality_role = (await db.execute(quality_role_stmt)).scalar_one_or_none()
        if not quality_role:
            qa_perms = [
                p for code, p in perm_map.items()
                if code.startswith("hr.") or code.startswith("kba.")
            ]
            quality_role = Role(
                code="ROLE_QUALITY_HEAD",
                name="质量与合规总监",
                description="ISO 9001 与 KBA 型式认证最高签批人，可跨部门审计",
                data_scope=DataScope.ALL,
                is_system=True,
                permissions=qa_perms
            )
            db.add(quality_role)
            await db.flush()

        # 部门经理角色
        dept_mgr_stmt = select(Role).where(Role.code == "ROLE_DEPT_MANAGER")
        dept_mgr = (await db.execute(dept_mgr_stmt)).scalar_one_or_none()
        if not dept_mgr:
            dept_perms = [
                perm_map.get("hr.department.read"),
                perm_map.get("hr.position.read"),
                perm_map.get("hr.employee.read"),
                perm_map.get("hr.cert.read")
            ]
            dept_mgr = Role(
                code="ROLE_DEPT_MANAGER",
                name="部门负责人",
                description="负责直属及下属部门日常业务审批与人员查看",
                data_scope=DataScope.DEPT_AND_CHILD,
                is_system=True,
                permissions=[p for p in dept_perms if p]
            )
            db.add(dept_mgr)
            await db.flush()

        # =====================================================================
        # 3. 种子化初始系统账号 (sys_users)
        # =====================================================================
        stmt_admin = select(User).options(selectinload(User.roles)).where(User.username == settings.INITIAL_SUPERUSER_USERNAME)
        admin = (await db.execute(stmt_admin)).scalar_one_or_none()
        if not admin:
            admin = User(
                username=settings.INITIAL_SUPERUSER_USERNAME,
                email=settings.INITIAL_SUPERUSER_EMAIL,
                full_name=settings.INITIAL_SUPERUSER_NAME,
                hashed_password=get_password_hash(settings.INITIAL_SUPERUSER_PASSWORD),
                role="admin",
                is_active=True,
                is_superuser=True,
                roles=[admin_role]
            )
            db.add(admin)
            logger.info(f"[SEED] 已创建默认超级管理员账号并绑定 ROLE_SUPER_ADMIN: '{settings.INITIAL_SUPERUSER_USERNAME}'")
        else:
            if admin_role not in admin.roles:
                admin.roles.append(admin_role)

        stmt_op = select(User).where(User.username == "operator")
        operator = (await db.execute(stmt_op)).scalar_one_or_none()
        if not operator:
            operator = User(
                username="operator",
                email="operator@bravio-erp.com",
                full_name="车间质检操作员",
                hashed_password=get_password_hash("operator123"),
                role="operator",
                is_active=True,
                is_superuser=False
            )
            db.add(operator)
            logger.info("[SEED] 已创建演示操作员: 'operator'")

        # =====================================================================
        # 4. 种子化组织架构部门树 (hr_departments - docs/04)
        # =====================================================================
        dept_root_stmt = select(Department).where(Department.code == "DEPT-HQ")
        dept_root = (await db.execute(dept_root_stmt)).scalar_one_or_none()
        if not dept_root:
            dept_root = Department(
                code="DEPT-HQ",
                name="Bravio 集团总部",
                iso_process_type=IsoProcessType.MANAGEMENT,
                sort_order=1,
                description="集团战略决策、质量管理体系与全球合规中枢"
            )
            db.add(dept_root)
            await db.flush()

            # 二级子部门
            dept_qa = Department(
                code="DEPT-QA",
                name="质量保证与法规合规中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=10,
                description="统辖 ISO 9001 质量管理与德国 KBA Type Approval 型式认证"
            )
            dept_mfg = Department(
                code="DEPT-MFG",
                name="先进制造与供应链中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=20,
                description="精密总装车间、贴片产线与全自动包装出库中心"
            )
            dept_rd = Department(
                code="DEPT-RD",
                name="研发与工程技术中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=30,
                description="硬件总成、嵌入式固件与汽车电子零部件工程设计"
            )
            db.add_all([dept_qa, dept_mfg, dept_rd])
            await db.flush()

            # =====================================================================
            # 5. 种子化岗位体系 (hr_job_positions)
            # =====================================================================
            pos_kba = JobPosition(
                code="POS-KBA-SPEC",
                title="KBA 生产一致性(CoP) 主任审核员",
                department_id=dept_qa.id,
                is_safety_critical=True,
                required_cert_types=["KBA_COP_LEAD_AUDITOR", "ISO9001_LEAD_AUDITOR"],
                description="负责德国 KBA 车规级型式认证产品生产一致性终审与签署"
            )
            pos_qc = JobPosition(
                code="POS-QC-TECH",
                title="总装首件检测与特殊特性质检员",
                department_id=dept_mfg.id,
                is_safety_critical=True,
                required_cert_types=["SPECIAL_CHARACTERISTIC_INSPECTOR"],
                description="针对刹车、转向与被动安全电子模块进行首件放行检验"
            )
            db.add_all([pos_kba, pos_qc])
            await db.flush()

            # =====================================================================
            # 6. 种子化员工与合规资质矩阵 (hr_employees & certifications)
            # =====================================================================
            now = datetime.now(timezone.utc)
            emp_kba = Employee(
                employee_no="BR-2026-001",
                name="张合规 (Dr. Zhang)",
                email="zhang.compliance@bravio-erp.com",
                phone="+49 170 8899001",
                department_id=dept_qa.id,
                job_id=pos_kba.id,
                status=EmployeeStatus.ACTIVE,
                hire_date=now - timedelta(days=365)
            )
            db.add(emp_kba)
            await db.flush()

            # 为该关键员工添加有效资质
            cert1 = EmployeeCertification(
                employee_id=emp_kba.id,
                cert_name="KBA 生产一致性主任审核员资格证书",
                cert_type="KBA_COP_LEAD_AUDITOR",
                cert_no="KBA-COP-2025-DE-9982",
                issuing_authority="TÜV SÜD Auto Service GmbH",
                issue_date=now - timedelta(days=180),
                expiry_date=now + timedelta(days=365), # 长期有效
                is_valid=True
            )
            cert2 = EmployeeCertification(
                employee_id=emp_kba.id,
                cert_name="ISO 9001:2015 质量管理体系主任审核员证书",
                cert_type="ISO9001_LEAD_AUDITOR",
                cert_no="IRCA-QMS-2024-8841",
                issuing_authority="IRCA / DEKRA",
                issue_date=now - timedelta(days=300),
                expiry_date=now + timedelta(days=20),  # 20天后即将到期（触发预警）
                is_valid=True
            )
            db.add_all([cert1, cert2])

        await db.commit()
        logger.info("[SEED] Bravio ERP v0.1 组织架构树、岗位体系与合规资质矩阵种子数据装载完成。")
