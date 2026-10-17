from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.organization import (
    Department,
    JobPosition,
    Employee,
    EmployeeCertification,
    EmployeeTraining,
    EmployeeStatus
)
from app.schemas.organization import (
    DepartmentTreeNode,
    EmployeeCompetencyAudit,
    CertificationResponse
)

class OrganizationService:
    @staticmethod
    async def get_department_tree(db: AsyncSession) -> List[DepartmentTreeNode]:
        """
        获取多级自引用部门树形结构，并附带员工人数统计
        """
        # 查询全部有效部门
        stmt = select(Department).where(Department.is_deleted == False).order_by(Department.sort_order.asc())
        result = await db.execute(stmt)
        depts = result.scalars().all()

        # 统计各部门在职员工人数
        count_stmt = (
            select(Employee.department_id, func.count(Employee.id))
            .where(Employee.is_deleted == False, Employee.status == EmployeeStatus.ACTIVE)
            .group_by(Employee.department_id)
        )
        count_res = await db.execute(count_stmt)
        dept_counts: Dict[str, int] = dict(count_res.all())

        # 构造节点字典
        node_map: Dict[str, DepartmentTreeNode] = {}
        for d in depts:
            node_map[d.id] = DepartmentTreeNode(
                id=d.id,
                code=d.code,
                name=d.name,
                parent_id=d.parent_id,
                manager_id=d.manager_id,
                iso_process_type=d.iso_process_type,
                sort_order=d.sort_order,
                description=d.description,
                created_at=d.created_at,
                children=[],
                employee_count=dept_counts.get(d.id, 0)
            )

        root_nodes: List[DepartmentTreeNode] = []
        for d in depts:
            curr_node = node_map[d.id]
            if d.parent_id and d.parent_id in node_map:
                node_map[d.parent_id].children.append(curr_node)
            else:
                root_nodes.append(curr_node)

        return root_nodes

    @staticmethod
    def audit_competency(employee: Employee, job: Optional[JobPosition]) -> EmployeeCompetencyAudit:
        """
        核心合规逻辑 (docs/04): 
        针对 ISO 9001 7.2 与 KBA Type Approval 关键安全岗位 (Special Characteristics)
        严格审查在岗人员资质证书矩阵，识别【缺失】、【已过期】、【到期预警】状态
        """
        if not job or not job.is_safety_critical:
            return EmployeeCompetencyAudit(
                is_compliant=True,
                is_safety_critical_job=False,
                notes="普通非关键安全工位，资质要求满足基础标准"
            )

        required_types = set(job.required_cert_types or [])
        now = datetime.now(timezone.utc)
        warning_delta = timedelta(days=30)

        held_active_types = set()
        missing_types = []
        expired_types = []
        warning_types = []

        for cert in (employee.certifications or []):
            if not cert.is_valid or cert.is_deleted:
                continue

            exp = cert.expiry_date
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            if now > exp:
                expired_types.append(f"{cert.cert_name} (编号: {cert.cert_no}) 已过期")
            else:
                held_active_types.add(cert.cert_type)
                if exp <= now + warning_delta:
                    days_left = (exp - now).days
                    warning_types.append(f"{cert.cert_name} (将在 {days_left} 天后到期)")

        for req in required_types:
            if req not in held_active_types:
                missing_types.append(req)

        is_compliant = (len(missing_types) == 0 and len(expired_types) == 0)

        notes_parts = []
        if not is_compliant:
            notes_parts.append("[合规风险阻断] 关键特殊特性工位资质不达标")
            if missing_types:
                notes_parts.append(f"缺少必需资质: {', '.join(missing_types)}")
            if expired_types:
                notes_parts.append(f"存在过期资质: {', '.join(expired_types)}")
        else:
            notes_parts.append("[合规受控] 关键特殊特性工位资质完备且有效")

        if warning_types:
            notes_parts.append(f"[预警] 30天内到期证书: {', '.join(warning_types)}")

        return EmployeeCompetencyAudit(
            is_compliant=is_compliant,
            is_safety_critical_job=True,
            missing_cert_types=missing_types,
            expired_cert_types=expired_types,
            warning_cert_types=warning_types,
            notes="; ".join(notes_parts)
        )

    @staticmethod
    async def get_expiring_certifications(db: AsyncSession, days: int = 30) -> List[EmployeeCertification]:
        """
        获取即将到期或已经过期的证书列表，支持合规预警大盘
        """
        now = datetime.now(timezone.utc)
        threshold = now + timedelta(days=days)

        stmt = (
            select(EmployeeCertification)
            .where(
                EmployeeCertification.is_deleted == False,
                EmployeeCertification.is_valid == True,
                EmployeeCertification.expiry_date <= threshold
            )
            .order_by(EmployeeCertification.expiry_date.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
