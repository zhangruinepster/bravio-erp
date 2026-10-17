from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, require_permissions
from app.models.user import User
from app.models.organization import (
    Department,
    JobPosition,
    Employee,
    EmployeeCertification,
    EmployeeTraining,
    EmployeeStatus
)
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeNode,
    JobPositionCreate,
    JobPositionUpdate,
    JobPositionResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeCompetencyAudit,
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
    TrainingCreate,
    TrainingResponse
)
from app.services.organization_service import OrganizationService

router = APIRouter()

# =========================================================================
# 1. 部门管理 (Departments & Tree)
# =========================================================================

@router.get("/departments", response_model=List[DepartmentResponse], summary="获取部门列表")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Department).where(Department.is_deleted == False).order_by(Department.sort_order.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/departments/tree", response_model=List[DepartmentTreeNode], summary="获取企业多级组织架构树")
async def get_department_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await OrganizationService.get_department_tree(db)

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, summary="创建新部门")
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("hr.department.create"))
):
    # 检查 code 唯一性
    exist_stmt = select(Department).where(Department.code == dept_in.code, Department.is_deleted == False)
    exist = (await db.execute(exist_stmt)).scalar_one_or_none()
    if exist:
        raise HTTPException(status_code=400, detail=f"部门编码 '{dept_in.code}' 已存在")

    dept = Department(
        code=dept_in.code,
        name=dept_in.name,
        parent_id=dept_in.parent_id,
        manager_id=dept_in.manager_id,
        iso_process_type=dept_in.iso_process_type,
        sort_order=dept_in.sort_order,
        description=dept_in.description,
        created_by_id=current_user.id
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

@router.put("/departments/{dept_id}", response_model=DepartmentResponse, summary="更新部门信息")
async def update_department(
    dept_id: str,
    dept_in: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("hr.department.update"))
):
    stmt = select(Department).where(Department.id == dept_id, Department.is_deleted == False)
    dept = (await db.execute(stmt)).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="目标部门不存在")

    update_data = dept_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dept, field, value)
    dept.updated_by_id = current_user.id

    await db.commit()
    await db.refresh(dept)
    return dept

# =========================================================================
# 2. 岗位管理 (Job Positions)
# =========================================================================

@router.get("/positions", response_model=List[JobPositionResponse], summary="获取岗位列表")
async def list_positions(
    department_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(JobPosition).where(JobPosition.is_deleted == False)
    if department_id:
        stmt = stmt.where(JobPosition.department_id == department_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/positions", response_model=JobPositionResponse, status_code=status.HTTP_201_CREATED, summary="创建岗位")
async def create_position(
    pos_in: JobPositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("hr.position.create"))
):
    exist_stmt = select(JobPosition).where(JobPosition.code == pos_in.code, JobPosition.is_deleted == False)
    if (await db.execute(exist_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"岗位编码 '{pos_in.code}' 已存在")

    pos = JobPosition(
        code=pos_in.code,
        title=pos_in.title,
        department_id=pos_in.department_id,
        is_safety_critical=pos_in.is_safety_critical,
        required_cert_types=pos_in.required_cert_types,
        description=pos_in.description,
        created_by_id=current_user.id
    )
    db.add(pos)
    await db.commit()
    await db.refresh(pos)
    return pos

# =========================================================================
# 3. 员工花名册 (Employees & Competency)
# =========================================================================

@router.get("/employees", response_model=List[EmployeeResponse], summary="获取员工列表")
async def list_employees(
    department_id: Optional[str] = None,
    status_filter: Optional[EmployeeStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Employee)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.job_position),
            selectinload(Employee.certifications),
            selectinload(Employee.trainings)
        )
        .where(Employee.is_deleted == False)
    )
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if status_filter:
        stmt = stmt.where(Employee.status == status_filter)

    result = await db.execute(stmt)
    employees = result.scalars().all()

    resp_list = []
    now = datetime.now(timezone.utc)
    for emp in employees:
        audit_res = OrganizationService.audit_competency(emp, emp.job_position)
        
        # 封装证书返回带预警属性
        cert_resps = []
        for c in emp.certifications:
            exp = c.expiry_date
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            is_exp = now > exp
            days = (exp - now).days
            cert_resps.append(
                CertificationResponse(
                    id=c.id,
                    employee_id=c.employee_id,
                    cert_name=c.cert_name,
                    cert_type=c.cert_type,
                    cert_no=c.cert_no,
                    issuing_authority=c.issuing_authority,
                    issue_date=c.issue_date,
                    expiry_date=c.expiry_date,
                    is_valid=c.is_valid,
                    attachment_url=c.attachment_url,
                    is_expired=is_exp,
                    days_to_expire=days,
                    is_warning=(not is_exp and days <= 30),
                    created_at=c.created_at
                )
            )

        # 提取绑定账号信息
        acc_username = emp.user.username if emp.user else None
        acc_roles = [r.name for r in getattr(emp.user, "roles", [])] if emp.user else []

        resp_list.append(
            EmployeeResponse(
                id=emp.id,
                employee_no=emp.employee_no,
                name=emp.name,
                email=emp.email,
                phone=emp.phone,
                department_id=emp.department_id,
                department_name=emp.department.name if emp.department else None,
                job_id=emp.job_id,
                job_title=emp.job_position.title if emp.job_position else None,
                manager_id=emp.manager_id,
                status=emp.status,
                hire_date=emp.hire_date,
                user_id=emp.user_id,
                account_username=acc_username,
                account_roles=acc_roles,
                created_at=emp.created_at,
                certifications=cert_resps,
                trainings=[TrainingResponse.model_validate(t) for t in emp.trainings],
                competency_status=audit_res
            )
        )
    return resp_list

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, summary="录入新员工(支持同时开通系统账号)")
async def create_employee(
    emp_in: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("hr.employee.create"))
):
    from app.core.security import get_password_hash
    from app.models.rbac import Role

    # 1. 检查工号与邮箱唯一性
    exist_no = (await db.execute(select(Employee).where(Employee.employee_no == emp_in.employee_no, Employee.is_deleted == False))).scalar_one_or_none()
    if exist_no:
        raise HTTPException(status_code=400, detail=f"工号 '{emp_in.employee_no}' 已被占用")

    exist_email = (await db.execute(select(Employee).where(Employee.email == emp_in.email, Employee.is_deleted == False))).scalar_one_or_none()
    if exist_email:
        raise HTTPException(status_code=400, detail=f"邮箱 '{emp_in.email}' 已被占用")

    created_user_id = emp_in.user_id
    acc_username = None
    acc_roles = []

    # 2. 如果提供了 account 信息，同步创建 sys_users 账号
    if emp_in.account and emp_in.account.username:
        acc = emp_in.account
        exist_u = (await db.execute(select(User).where(User.username == acc.username, User.is_deleted == False))).scalar_one_or_none()
        if exist_u:
            raise HTTPException(status_code=400, detail=f"系统登录用户名 '{acc.username}' 已被占用")

        # 密码强度简易核验
        if len(acc.password) < 6:
            raise HTTPException(status_code=400, detail="登录密码长度至少为 6 位")

        new_user = User(
            username=acc.username,
            email=str(emp_in.email),
            full_name=emp_in.name,
            hashed_password=get_password_hash(acc.password),
            role="operator",
            is_active=acc.is_active,
            is_superuser=False,
            created_by_id=current_user.id
        )

        if acc.role_ids:
            roles_stmt = select(Role).where(Role.id.in_(acc.role_ids), Role.is_deleted == False)
            assigned_roles = (await db.execute(roles_stmt)).scalars().all()
            new_user.roles = list(assigned_roles)
            acc_roles = [r.name for r in assigned_roles]

        db.add(new_user)
        await db.flush()
        created_user_id = new_user.id
        acc_username = new_user.username

    # 3. 创建员工人事实体
    emp = Employee(
        employee_no=emp_in.employee_no,
        name=emp_in.name,
        email=emp_in.email,
        phone=emp_in.phone,
        department_id=emp_in.department_id,
        job_id=emp_in.job_id,
        manager_id=emp_in.manager_id,
        status=emp_in.status,
        hire_date=emp_in.hire_date,
        user_id=created_user_id,
        created_by_id=current_user.id
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    return EmployeeResponse(
        id=emp.id,
        employee_no=emp.employee_no,
        name=emp.name,
        email=emp.email,
        phone=emp.phone,
        department_id=emp.department_id,
        job_id=emp.job_id,
        manager_id=emp.manager_id,
        status=emp.status,
        hire_date=emp.hire_date,
        user_id=emp.user_id,
        account_username=acc_username,
        account_roles=acc_roles,
        created_at=emp.created_at,
        certifications=[],
        trainings=[]
    )


# =========================================================================
# 4. 资质认证与预警 (Certifications)
# =========================================================================

@router.get("/certifications/expiring", response_model=List[CertificationResponse], summary="获取30天内到期或已过期的资质预警列表")
async def get_expiring_certifications(
    days: int = Query(30, description="预警窗口天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    certs = await OrganizationService.get_expiring_certifications(db, days=days)
    now = datetime.now(timezone.utc)
    resps = []
    for c in certs:
        exp = c.expiry_date
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        is_exp = now > exp
        days_left = (exp - now).days
        resps.append(
            CertificationResponse(
                id=c.id,
                employee_id=c.employee_id,
                cert_name=c.cert_name,
                cert_type=c.cert_type,
                cert_no=c.cert_no,
                issuing_authority=c.issuing_authority,
                issue_date=c.issue_date,
                expiry_date=c.expiry_date,
                is_valid=c.is_valid,
                attachment_url=c.attachment_url,
                is_expired=is_exp,
                days_to_expire=days_left,
                is_warning=(not is_exp and days_left <= days),
                created_at=c.created_at
            )
        )
    return resps

@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED, summary="为员工登记资质证书")
async def create_certification(
    cert_in: CertificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("hr.cert.create"))
):
    cert = EmployeeCertification(
        employee_id=cert_in.employee_id,
        cert_name=cert_in.cert_name,
        cert_type=cert_in.cert_type,
        cert_no=cert_in.cert_no,
        issuing_authority=cert_in.issuing_authority,
        issue_date=cert_in.issue_date,
        expiry_date=cert_in.expiry_date,
        is_valid=cert_in.is_valid,
        attachment_url=cert_in.attachment_url,
        created_by_id=current_user.id
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)

    now = datetime.now(timezone.utc)
    exp = cert.expiry_date
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    is_exp = now > exp
    days = (exp - now).days

    return CertificationResponse(
        id=cert.id,
        employee_id=cert.employee_id,
        cert_name=cert.cert_name,
        cert_type=cert.cert_type,
        cert_no=cert.cert_no,
        issuing_authority=cert.issuing_authority,
        issue_date=cert.issue_date,
        expiry_date=cert.expiry_date,
        is_valid=cert.is_valid,
        attachment_url=cert.attachment_url,
        is_expired=is_exp,
        days_to_expire=days,
        is_warning=(not is_exp and days <= 30),
        created_at=cert.created_at
    )
