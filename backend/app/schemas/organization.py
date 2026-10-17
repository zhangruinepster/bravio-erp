from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.organization import IsoProcessType, EmployeeStatus

# ----------------- 部门模型 -----------------
class DepartmentBase(BaseModel):
    code: str
    name: str
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    iso_process_type: IsoProcessType = IsoProcessType.CORE
    sort_order: int = 0
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    iso_process_type: Optional[IsoProcessType] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DepartmentTreeNode(DepartmentResponse):
    children: List["DepartmentTreeNode"] = []
    employee_count: int = 0

# ----------------- 岗位模型 -----------------
class JobPositionBase(BaseModel):
    code: str
    title: str
    department_id: str
    is_safety_critical: bool = False
    required_cert_types: List[str] = []
    description: Optional[str] = None

class JobPositionCreate(JobPositionBase):
    pass

class JobPositionUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[str] = None
    is_safety_critical: bool = None
    required_cert_types: Optional[List[str]] = None
    description: Optional[str] = None

class JobPositionResponse(JobPositionBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- 资质证书模型 -----------------
class CertificationBase(BaseModel):
    cert_name: str
    cert_type: str
    cert_no: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    is_valid: bool = True
    attachment_url: Optional[str] = None

class CertificationCreate(CertificationBase):
    employee_id: str

class CertificationUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_no: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_valid: Optional[bool] = None
    attachment_url: Optional[str] = None

class CertificationResponse(CertificationBase):
    id: str
    employee_id: str
    is_expired: bool
    days_to_expire: int
    is_warning: bool = False # 30天内到期预警
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- 培训履历模型 -----------------
class TrainingBase(BaseModel):
    training_topic: str
    training_date: datetime
    hours: float = 1.0
    trainer: Optional[str] = None
    score: Optional[float] = None
    is_passed: bool = True
    effectiveness_evaluation: Optional[str] = None

class TrainingCreate(TrainingBase):
    employee_id: str

class TrainingResponse(TrainingBase):
    id: str
    employee_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- 员工花名册模型 -----------------
class EmployeeAccountCreate(BaseModel):
    """为员工直接创建关联的系统登录账号与角色 (docs/03 & docs/04)"""
    username: str
    password: str
    role_ids: List[str] = []
    is_active: bool = True

class EmployeeBase(BaseModel):
    employee_no: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: str
    job_id: Optional[str] = None
    manager_id: Optional[str] = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    hire_date: Optional[datetime] = None
    user_id: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    account: Optional[EmployeeAccountCreate] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    job_id: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    hire_date: Optional[datetime] = None
    user_id: Optional[str] = None

class EmployeeCompetencyAudit(BaseModel):
    """关键岗位资质合规性审查结论"""
    is_compliant: bool
    is_safety_critical_job: bool
    missing_cert_types: List[str] = []
    expired_cert_types: List[str] = []
    warning_cert_types: List[str] = []
    notes: str

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    department_name: Optional[str] = None
    job_title: Optional[str] = None
    account_username: Optional[str] = None
    account_roles: List[str] = []
    certifications: List[CertificationResponse] = []
    trainings: List[TrainingResponse] = []
    competency_status: Optional[EmployeeCompetencyAudit] = None
    model_config = ConfigDict(from_attributes=True)

