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
from app.models import (
    ProductMaster,
    ProductLifecycleStatus,
    BillOfMaterial,
    BomItem,
    PackagingHierarchy,
    BomComponentCategory,
    BarcodeRule,
    BarcodeLevel,
    ControlledDocument,
    IsoDocLevel,
    DocStatus,
    BusinessPartner,
    PartnerType,
    SystemAttachment
)
from app.core.generate_demo_assets import create_demo_assets
import os, hashlib

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
    # 产品与工程模块权限 (预备给产品工程师)
    ("product.item.read", "查看产品物料主数据", "product", "查询产品图号、规格与BOM"),
    ("product.item.create", "创建产品物料", "product", "定义新产品物料与规格参数"),
    ("product.bom.manage", "管理产品BOM架构", "product", "维护产品多级BOM与替代料"),
    # 质量与8D管理权限 (预备给质量工程师)
    ("qms.inspection.read", "查看质量检验单据", "qms", "浏览进料/过程/出货质检报告"),
    ("qms.inspection.create", "执行首件与过程质检", "qms", "录入特殊特性尺寸与抽检数据"),
    ("qms.incident.8d", "发起8D异常客诉攻关", "qms", "组织质量异常分析与纠正预防CAPA"),
    # 供应商与制造执行权限 (预备给供应商专员)
    ("srm.supplier.read", "查看供应商档案", "srm", "查询供应商资质与供货清单"),
    ("srm.delivery.confirm", "确认供应商送货与发运", "srm", "协同供应商外协送货与批次交接"),
    # 系统与运维安全权限 (仅限系统超级管理员)
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
        # 2. 种子化组织架构部门树 (hr_departments)
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

        dept_qa_stmt = select(Department).where(Department.code == "DEPT-QA")
        dept_qa = (await db.execute(dept_qa_stmt)).scalar_one_or_none()
        if not dept_qa:
            dept_qa = Department(
                code="DEPT-QA",
                name="质量保证与法规合规中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=10,
                description="统辖 ISO 9001 质量管理与德国 KBA Type Approval 型式认证"
            )
            db.add(dept_qa)
            await db.flush()

        dept_mfg_stmt = select(Department).where(Department.code == "DEPT-MFG")
        dept_mfg = (await db.execute(dept_mfg_stmt)).scalar_one_or_none()
        if not dept_mfg:
            dept_mfg = Department(
                code="DEPT-MFG",
                name="先进制造与供应链中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=20,
                description="精密总装车间、贴片产线与全自动包装出库中心"
            )
            db.add(dept_mfg)
            await db.flush()

        dept_rd_stmt = select(Department).where(Department.code == "DEPT-RD")
        dept_rd = (await db.execute(dept_rd_stmt)).scalar_one_or_none()
        if not dept_rd:
            dept_rd = Department(
                code="DEPT-RD",
                name="研发与工程技术中心",
                parent_id=dept_root.id,
                iso_process_type=IsoProcessType.CORE,
                sort_order=30,
                description="硬件总成、嵌入式固件与汽车电子零部件工程设计"
            )
            db.add(dept_rd)
            await db.flush()

        # =====================================================================
        # 3. 种子化岗位体系 (hr_job_positions)
        # =====================================================================
        pos_dict = {}
        target_positions = [
            ("POS-GM", "集团总经理兼执行委员会主席", dept_root.id, False, [], "全面主持企业经营与各业务流推进"),
            ("POS-PE-LEAD", "产品研发与硬件工程主管", dept_rd.id, False, [], "负责汽车电子产品结构、硬件BOM与技术图谱设计"),
            ("POS-QE-LEAD", "汽车特殊特性与首件质量工程师", dept_qa.id, True, ["ISO9001_INTERNAL_AUDITOR", "SPECIAL_CHARACTERISTIC_INSPECTOR"], "负责关键特殊特性工位首件放行与过程合规"),
            ("POS-SUP-LEAD", "供应链采购与外协制造主管", dept_mfg.id, False, [], "负责外协零部件协同交期、来料追溯与供应商评价"),
            ("POS-KBA-SPEC", "KBA 生产一致性(CoP) 主任审核员", dept_qa.id, True, ["KBA_COP_LEAD_AUDITOR", "ISO9001_LEAD_AUDITOR"], "负责德国 KBA 车规级型式认证产品生产一致性终审")
        ]
        for p_code, p_title, p_dept_id, p_critical, p_certs, p_desc in target_positions:
            p_stmt = select(JobPosition).where(JobPosition.code == p_code)
            pos_obj = (await db.execute(p_stmt)).scalar_one_or_none()
            if not pos_obj:
                pos_obj = JobPosition(
                    code=p_code,
                    title=p_title,
                    department_id=p_dept_id,
                    is_safety_critical=p_critical,
                    required_cert_types=p_certs,
                    description=p_desc
                )
                db.add(pos_obj)
                await db.flush()
            pos_dict[p_code] = pos_obj

        # =====================================================================
        # 4. 种子化立体角色 (sys_roles)
        # =====================================================================
        # 4.1 超级管理员角色
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

        # 4.2 总经理角色 (全业务模块，但绝无底层系统运维日志权限)
        gm_role_stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code == "ROLE_GENERAL_MANAGER")
        gm_role = (await db.execute(gm_role_stmt)).scalar_one_or_none()
        if not gm_role:
            # 排除 system.* 权限，拥有全部业务权限
            gm_perms = [p for code, p in perm_map.items() if not code.startswith("system.")]
            gm_role = Role(
                code="ROLE_GENERAL_MANAGER",
                name="集团总经理",
                description="拥有企业全部业务模块管理与查看权限 (无后台系统运维权限)",
                data_scope=DataScope.ALL,
                is_system=True,
                permissions=gm_perms
            )
            db.add(gm_role)
            await db.flush()

        # 4.3 产品工程师角色
        pe_role_stmt = select(Role).where(Role.code == "ROLE_PRODUCT_ENGINEER")
        pe_role = (await db.execute(pe_role_stmt)).scalar_one_or_none()
        if not pe_role:
            pe_perms = [
                perm_map.get("hr.employee.read"),
                perm_map.get("hr.department.read"),
                perm_map.get("product.item.read"),
                perm_map.get("product.item.create"),
                perm_map.get("product.bom.manage")
            ]
            pe_role = Role(
                code="ROLE_PRODUCT_ENGINEER",
                name="产品工程师",
                description="负责产品物料主数据定义、图号规格与多级 BOM 管理",
                data_scope=DataScope.DEPT_AND_CHILD,
                is_system=True,
                permissions=[p for p in pe_perms if p]
            )
            db.add(pe_role)
            await db.flush()

        # 4.4 质量工程师角色
        qe_role_stmt = select(Role).where(Role.code == "ROLE_QUALITY_ENGINEER")
        qe_role = (await db.execute(qe_role_stmt)).scalar_one_or_none()
        if not qe_role:
            qe_perms = [
                perm_map.get("hr.employee.read"),
                perm_map.get("hr.cert.read"),
                perm_map.get("kba.cop.audit"),
                perm_map.get("qms.inspection.read"),
                perm_map.get("qms.inspection.create"),
                perm_map.get("qms.incident.8d")
            ]
            qe_role = Role(
                code="ROLE_QUALITY_ENGINEER",
                name="质量工程师",
                description="负责 ISO 9001 与 KBA 首件质量放行检验与 8D 攻关",
                data_scope=DataScope.DEPT_AND_CHILD,
                is_system=True,
                permissions=[p for p in qe_perms if p]
            )
            db.add(qe_role)
            await db.flush()

        # 4.5 供应商专员角色
        sup_role_stmt = select(Role).where(Role.code == "ROLE_SUPPLIER_USER")
        sup_role = (await db.execute(sup_role_stmt)).scalar_one_or_none()
        if not sup_role:
            sup_perms = [
                perm_map.get("hr.department.read"),
                perm_map.get("srm.supplier.read"),
                perm_map.get("srm.delivery.confirm")
            ]
            sup_role = Role(
                code="ROLE_SUPPLIER_USER",
                name="供应商专员",
                description="负责外协制造生产进度确认、来料批次交接与协同",
                data_scope=DataScope.DEPT_ONLY,
                is_system=True,
                permissions=[p for p in sup_perms if p]
            )
            db.add(sup_role)
            await db.flush()

        # =====================================================================
        # 5. 清理已废弃的旧车间质检员 operator 账号 (满足需求 1)
        # =====================================================================
        old_op = (await db.execute(select(User).where(User.username == "operator"))).scalar_one_or_none()
        if old_op:
            await db.delete(old_op)
            logger.info("[SEED] 已彻底删除旧的测试账号: operator")

        old_op_emp = (await db.execute(select(Employee).where(Employee.employee_no == "BR-2026-OP"))).scalar_one_or_none()
        if old_op_emp:
            await db.delete(old_op_emp)

        # =====================================================================
        # 6. 种子化真实人事员工与其系统登录账号 (满足需求 2, 3, 4, 5)
        # =====================================================================
        # 6.1 系统总管理员
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
            await db.flush()
        else:
            if admin_role not in admin.roles:
                admin.roles.append(admin_role)

        # 真实员工与账号配置列表
        real_accounts = [
            # (username, password, full_name, email, role_obj, is_superuser, app_role, emp_no, dept_id, pos_id)
            ("gm", "gm123", "陈总裁 (Chen GM)", "gm@bravio-erp.com", gm_role, False, "manager",
             "BR-2026-000", dept_root.id, pos_dict["POS-GM"].id),
            ("pe", "pe123", "王工程 (Wang PE)", "pe@bravio-erp.com", pe_role, False, "operator",
             "BR-2026-101", dept_rd.id, pos_dict["POS-PE-LEAD"].id),
            ("qe", "qe123", "刘质保 (Liu QE)", "qe@bravio-erp.com", qe_role, False, "operator",
             "BR-2026-201", dept_qa.id, pos_dict["POS-QE-LEAD"].id),
            ("supplier", "supplier123", "张供应 (Zhang Supplier)", "supplier@bravio-erp.com", sup_role, False, "operator",
             "BR-2026-301", dept_mfg.id, pos_dict["POS-SUP-LEAD"].id),
        ]

        now = datetime.now(timezone.utc)
        for u_name, u_pass, f_name, u_email, r_obj, is_super, app_r, e_no, d_id, p_id in real_accounts:
            # 查找或创建 User
            u_stmt = select(User).options(selectinload(User.roles)).where(User.username == u_name)
            u_obj = (await db.execute(u_stmt)).scalar_one_or_none()
            if not u_obj:
                u_obj = User(
                    username=u_name,
                    email=u_email,
                    full_name=f_name,
                    hashed_password=get_password_hash(u_pass),
                    role=app_r,
                    is_active=True,
                    is_superuser=is_super,
                    roles=[r_obj]
                )
                db.add(u_obj)
                await db.flush()
                logger.info(f"[SEED] 已创建系统账号: {u_name} ({f_name})")
            else:
                u_obj.hashed_password = get_password_hash(u_pass)
                u_obj.is_active = True
                u_obj.is_superuser = is_super
                u_obj.role = app_r
                if r_obj not in u_obj.roles:
                    u_obj.roles.append(r_obj)

            # 查找或创建对应 Employee 人事档案
            e_stmt = select(Employee).where(Employee.employee_no == e_no)
            e_obj = (await db.execute(e_stmt)).scalar_one_or_none()
            if not e_obj:
                e_obj = Employee(
                    employee_no=e_no,
                    name=f_name,
                    email=u_email,
                    department_id=d_id,
                    job_id=p_id,
                    status=EmployeeStatus.ACTIVE,
                    hire_date=now - timedelta(days=200),
                    user_id=u_obj.id
                )
                db.add(e_obj)
                await db.flush()
                logger.info(f"[SEED] 已创建对应人事档案: {e_no} ({f_name})")

                # 如果是质量工程师，为其配备特殊特性与 ISO 资质证书
                if u_name == "qe":
                    cert_qe = EmployeeCertification(
                        employee_id=e_obj.id,
                        cert_name="汽车特殊特性(SC/CC) 质量放行工程师资格",
                        cert_type="SPECIAL_CHARACTERISTIC_INSPECTOR",
                        cert_no="QE-SC-2025-099",
                        issuing_authority="Bravio 质量与合规技术委员会",
                        issue_date=now - timedelta(days=90),
                        expiry_date=now + timedelta(days=275),
                        is_valid=True
                    )
                    db.add(cert_qe)

        # 6.2 原有 KBA 主任审核员档案 (BR-2026-001)
        emp_kba_stmt = select(Employee).where(Employee.employee_no == "BR-2026-001")
        emp_kba = (await db.execute(emp_kba_stmt)).scalar_one_or_none()
        if not emp_kba:
            emp_kba = Employee(
                employee_no="BR-2026-001",
                name="张合规 (Dr. Zhang)",
                email="zhang.compliance@bravio-erp.com",
                phone="+49 170 8899001",
                department_id=dept_qa.id,
                job_id=pos_dict["POS-KBA-SPEC"].id,
                status=EmployeeStatus.ACTIVE,
                hire_date=now - timedelta(days=365)
            )
            db.add(emp_kba)
            await db.flush()

            cert1 = EmployeeCertification(
                employee_id=emp_kba.id,
                cert_name="KBA 生产一致性主任审核员资格证书",
                cert_type="KBA_COP_LEAD_AUDITOR",
                cert_no="KBA-COP-2025-DE-9982",
                issuing_authority="TÜV SÜD Auto Service GmbH",
                issue_date=now - timedelta(days=180),
                expiry_date=now + timedelta(days=365),
                is_valid=True
            )
            cert2 = EmployeeCertification(
                employee_id=emp_kba.id,
                cert_name="ISO 9001:2015 质量管理体系主任审核员证书",
                cert_type="ISO9001_LEAD_AUDITOR",
                cert_no="IRCA-QMS-2024-8841",
                issuing_authority="IRCA / DEKRA",
                issue_date=now - timedelta(days=300),
                expiry_date=now + timedelta(days=20),
                is_valid=True
            )
            db.add_all([cert1, cert2])

        # =====================================================================
        # 7. 种子化 V0.3 核心业务数据 (docs/05 ~ docs/17)
        # =====================================================================
        # 7.1 预设产品主数据 (99824)
        p_stmt = select(ProductMaster).where(ProductMaster.bravio_id == "99824")
        prod = (await db.execute(p_stmt)).scalar_one_or_none()
        if not prod:
            prod = ProductMaster(
                bravio_id="99824",
                product_name="LED Matrix Headlight Module Gen 2 (高配矩阵大灯总成)",
                current_revision="A",
                category="HEADLIGHT",
                is_certified=True,
                kba_approval_number="E1-149R-001234",
                homologation_authority="KBA-Flensburg (德国联邦机动车局)",
                iso_classification="SAFETY_RELEVANT",
                is_serialized=True,
                standard_warranty_months=36,
                lifecycle_status=ProductLifecycleStatus.PPAP_SIGN_OFF,
                current_phase_gate=4,
                notes="Bravio 核心旗舰车规大灯，支持高精度 32 位激光打码与一盒双灯配对"
            )
            db.add(prod)
            await db.flush()

            # 7.2 预设轻量 BOM 与出货包装层级
            bom = BillOfMaterial(
                product_id=prod.id,
                version="V1.0",
                description="Gen 2 首发量产版工程物料清单",
                is_active=True
            )
            db.add(bom)
            await db.flush()

            item1 = BomItem(
                bom_id=bom.id,
                part_number="OPT-LENS-9982",
                part_name="高透光光学矩阵透镜总成",
                category=BomComponentCategory.ASSEMBLY,
                quantity=1.0,
                unit="SET",
                reference_designator="LENS-FRONT",
                is_safety_critical=True
            )
            item2 = BomItem(
                bom_id=bom.id,
                part_number="LED-PCB-4401",
                part_name="OSRAM 车规大功率 LED 驱动板 (SMD)",
                category=BomComponentCategory.PART,
                quantity=1.0,
                unit="PCS",
                reference_designator="PCB-MAIN",
                is_safety_critical=True
            )
            item3 = BomItem(
                bom_id=bom.id,
                part_number="DOC-MANUAL-DE",
                part_name="德国 KBA 型式认证出厂合格证与多国语言说明书",
                category=BomComponentCategory.MANUAL,
                quantity=1.0,
                unit="PCS",
                is_safety_critical=False
            )
            item4 = BomItem(
                bom_id=bom.id,
                part_number="PKG-BOX-FOAM",
                part_name="定制高密度防静电双灯吸塑彩盒 (带防伪拉线)",
                category=BomComponentCategory.PACKAGING,
                quantity=1.0,
                unit="PCS",
                is_safety_critical=False
            )
            db.add_all([item1, item2, item3, item4])

            pkg = PackagingHierarchy(
                bom_id=bom.id,
                pieces_per_box=2,
                boxes_per_carton=20,
                cartons_per_pallet=24,
                box_spec="220x150x80mm",
                carton_spec="620x450x340mm",
                notes="一盒双支配对出货，单外箱 40 支，单托盘 960 支"
            )
            db.add(pkg)

        # 7.3 预设条码规则
        b_stmt = select(BarcodeRule).where(BarcodeRule.level == BarcodeLevel.SN)
        if not (await db.execute(b_stmt)).scalar_one_or_none():
            rule_sn = BarcodeRule(
                name="32位激光微距码标准规则 (车规激光刻码)",
                level=BarcodeLevel.SN,
                template="{BRAVIO_ID}{REV}{YEAR_WEEK}{SEQ}{BIN}",
                regex_pattern=r"^[0-9]{5}[A-Z][0-9]{4}[0-9]{8}[A-Z0-9]{14}$",
                is_default=True,
                description="汽车电子微型激光刻印标准: 5位零件号+1位版本+4位年周+8位流水+14位Binning"
            )
            rule_box = BarcodeRule(
                name="彩盒出运聚合条码 (双灯配对盒)",
                level=BarcodeLevel.BOX,
                template="BOX-{BRAVIO_ID}-{YEAR_WEEK}-{SEQ}",
                regex_pattern=r"^BOX-[0-9]{5}-[0-9]{4}-[0-9]{6}$",
                is_default=True,
                description="彩盒包装防拆标签码"
            )
            db.add_all([rule_sn, rule_box])

        # 7.4 预设受控体系文档 (ISO 9001 四层金字塔成文信息)
        d_stmt = select(ControlledDocument).where(ControlledDocument.doc_number == "QM-001")
        if not (await db.execute(d_stmt)).scalar_one_or_none():
            doc1 = ControlledDocument(
                doc_number="QM-001",
                title="Bravio 集团 ISO 9001:2015 质量管理手册 (最高纲领)",
                doc_level=IsoDocLevel.LEVEL_1_MANUAL,
                version="V3.0",
                department_scope="ALL",
                status=DocStatus.APPROVED_EFFECTIVE,
                summary="界定企业质量管理体系范围、过程图谱与德国 KBA Type Approval 生产一致性责任"
            )
            doc2 = ControlledDocument(
                doc_number="WI-QA-001",
                title="车灯装配线 32 位激光打码与一盒双支防呆检验作业指导书",
                doc_level=IsoDocLevel.LEVEL_3_WI,
                version="V2.1",
                department_scope="先进制造与供应链中心",
                status=DocStatus.APPROVED_EFFECTIVE,
                summary="规范包装工位 100% Binning 色温/光通量/电压参数比对与声光拦截操作"
            )
            db.add_all([doc1, doc2])

        # 7.5 预设商业伙伴档案 (代工厂与客户)
        bp_stmt = select(BusinessPartner).where(BusinessPartner.partner_code == "SUP-OEM-01")
        if not (await db.execute(bp_stmt)).scalar_one_or_none():
            sup = BusinessPartner(
                partner_code="SUP-OEM-01",
                name="德国德累斯顿精密微电子制造有限公司 (Dresden MicroTech GmbH)",
                partner_type=PartnerType.SUPPLIER,
                contact_person="Klaus Richter",
                contact_email="klaus.richter@dresden-microtech.de",
                contact_phone="+49 351 889900",
                is_oem_certified=True,
                api_token="m2m_dresden_oem_prod_token_2026",
                payment_terms_days=60,
                shipping_address="Dresden Silicon Park 18, 01109 Dresden, Germany",
                is_active=True,
                notes="具备 IATF 16949 与 KBA CoP 认可的外协代工厂"
            )
            cust = BusinessPartner(
                partner_code="CUST-OEM-01",
                name="巴伐利亚汽车工业集团研发与售后中心 (Bavaria Auto Group AG)",
                partner_type=PartnerType.CUSTOMER,
                contact_person="Stefan Weber",
                contact_email="stefan.weber@bavaria-auto.de",
                contact_phone="+49 89 382000",
                is_oem_certified=False,
                payment_terms_days=45,
                shipping_address="Petuelring 130, 80788 Munich, Germany",
                is_active=True,
                notes="前装车规级一级配套采购商"
            )
            db.add_all([sup, cust])

        # =====================================================================
        # 8. 种子化受控多媒体附件与 Demo 素材绑定 (docs/04, docs/10, docs/15)
        # =====================================================================
        create_demo_assets()

        # 8.1 绑定员工头像
        emp_avatars = {
            "BR-2026-001": ("avatar_dr_zhang.svg", "张合规博士 (Dr. Zhang) 官方合规认证档案照片"),
            "BR-2026-000": ("avatar_chen_gm.svg", "陈总裁 (Chen GM) 高管电子证件照"),
            "BR-2026-101": ("avatar_wang_pe.svg", "王工程 (Wang PE) 硬件研发主管工卡照片"),
            "BR-2026-201": ("avatar_liu_qe.svg", "刘质保 (Liu QE) 质量工程师工卡照片"),
            "BR-2026-301": ("avatar_default.svg", "张供应 (Zhang Supplier) 业务专员标准档案照片"),
        }
        for e_num, (svg_file, desc) in emp_avatars.items():
            emp_rec = (await db.execute(select(Employee).where(Employee.employee_no == e_num))).scalar_one_or_none()
            if emp_rec:
                if not emp_rec.avatar_url:
                    emp_rec.avatar_url = f"/uploads/demo/{svg_file}"
                att_exist = (await db.execute(select(SystemAttachment).where(
                    SystemAttachment.res_model == "hr_employee",
                    SystemAttachment.res_id == emp_rec.id
                ))).scalars().first()
                if not att_exist:
                    p_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "demo", svg_file))
                    sz = os.path.getsize(p_file) if os.path.exists(p_file) else 1024
                    hsh = hashlib.sha256(open(p_file, "rb").read()).hexdigest() if os.path.exists(p_file) else "hash_demo"
                    db.add(SystemAttachment(
                        file_name=svg_file,
                        stored_name=f"demo_{svg_file}",
                        content_type="image/svg+xml",
                        file_size=sz,
                        file_path=p_file,
                        file_url=f"/uploads/demo/{svg_file}",
                        sha256_hash=hsh,
                        res_model="hr_employee",
                        res_id=emp_rec.id,
                        description=desc
                    ))

        # 8.2 补充更多车规级产品物料并绑定实物设计图 (docs/10)
        demo_products = [
            ("99824", "LED Matrix Headlight Module Gen 2 (高配矩阵大灯总成)", "HEADLIGHT", "product_matrix_led.svg", "E1-149R-001234", "高配矩阵大灯总成实物渲染图"),
            ("99825", "Dynamic Daytime Running Light (流水日行灯带模块)", "DRL", "product_drl_module.svg", "E1-148R-005678", "动态流水日行灯光学外观设计图"),
            ("99826", "Aero Continuous OLED Tail Lamp (贯穿式尾灯总成)", "TAILLIGHT", "product_taillight_bar.svg", "E1-150R-009911", "贯穿式空气动力学尾灯总成图"),
            ("99827", "CAN-FD Multi-channel LED Matrix Driver Board", "DRIVER_BOARD", "product_driver_board.svg", "E1-10R-004321", "高频车规级矩阵驱动主板工程装配图"),
        ]
        for p_id, p_name, p_cat, p_svg, p_kba, p_desc in demo_products:
            p_obj = (await db.execute(select(ProductMaster).where(ProductMaster.bravio_id == p_id))).scalar_one_or_none()
            if not p_obj:
                p_obj = ProductMaster(
                    bravio_id=p_id,
                    product_name=p_name,
                    category=p_cat,
                    current_revision="A",
                    primary_image_url=f"/uploads/demo/{p_svg}",
                    is_certified=True,
                    kba_approval_number=p_kba,
                    homologation_authority="KBA-Flensburg (德国联邦机动车局)",
                    iso_classification="SAFETY_RELEVANT",
                    is_serialized=True,
                    standard_warranty_months=36,
                    lifecycle_status=ProductLifecycleStatus.PPAP_SIGN_OFF,
                    current_phase_gate=3,
                    notes=p_desc
                )
                db.add(p_obj)
                await db.flush()
            elif not p_obj.primary_image_url:
                p_obj.primary_image_url = f"/uploads/demo/{p_svg}"

            att_exist = (await db.execute(select(SystemAttachment).where(
                SystemAttachment.res_model == "product_master",
                SystemAttachment.res_id == p_obj.id
            ))).scalars().first()
            if not att_exist:
                p_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "demo", p_svg))
                sz = os.path.getsize(p_file) if os.path.exists(p_file) else 2048
                hsh = hashlib.sha256(open(p_file, "rb").read()).hexdigest() if os.path.exists(p_file) else "hash_prod_demo"
                db.add(SystemAttachment(
                    file_name=p_svg,
                    stored_name=f"demo_{p_svg}",
                    content_type="image/svg+xml",
                    file_size=sz,
                    file_path=p_file,
                    file_url=f"/uploads/demo/{p_svg}",
                    sha256_hash=hsh,
                    res_model="product_master",
                    res_id=p_obj.id,
                    description=p_desc
                ))

        await db.commit()
        logger.info("[SEED] Bravio ERP v0.3.2 全模块业务数据 (Product, BOM, Barcode, DMS, Partners, Attachments) 种子数据装载完成。")

