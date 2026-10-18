import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel

class IsoProcessType(str, enum.Enum):
    """ISO 9001 过程分类"""
    CORE = "CORE"               # 核心过程 (产品实现、生产组装、检验发运)
    MANAGEMENT = "MANAGEMENT"   # 管理过程 (管理评审、内审、风险控制)
    SUPPORT = "SUPPORT"         # 支持过程 (人力培训、设备计量、IT中枢)

class EmployeeStatus(str, enum.Enum):
    """员工全生命周期状态"""
    DRAFT = "DRAFT"             # 待入职/草拟
    PROBATION = "PROBATION"     # 试用期
    ACTIVE = "ACTIVE"           # 正式在职
    ON_LEAVE = "ON_LEAVE"       # 休假中
    RESIGNED = "RESIGNED"       # 已离职

class Department(BaseAuditModel):
    """
    部门组织树 (多级自引用树形结构 - docs/04)
    """
    __tablename__ = "hr_departments"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(String(36), ForeignKey("hr_departments.id", ondelete="SET NULL"), nullable=True)
    manager_id = Column(String(36), nullable=True)
    iso_process_type = Column(SQLEnum(IsoProcessType), default=IsoProcessType.CORE, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)

    # 树形关系与子级
    parent = relationship("Department", remote_side="Department.id", backref="children")
    positions = relationship("JobPosition", back_populates="department", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department code={self.code} name={self.name}>"

class JobPosition(BaseAuditModel):
    """
    岗位体系，严格把控 ISO 9001 与 KBA 关键特殊特性 (Special Characteristics) 工位
    """
    __tablename__ = "hr_job_positions"

    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    department_id = Column(String(36), ForeignKey("hr_departments.id", ondelete="CASCADE"), nullable=False)
    is_safety_critical = Column(Boolean, default=False, nullable=False)  # 是否关键安全工位
    required_cert_types = Column(JSON, default=list, nullable=False)     # 必须持有的证书类型编码列表
    description = Column(Text, nullable=True)

    department = relationship("Department", back_populates="positions")
    employees = relationship("Employee", back_populates="job_position")

    def __repr__(self):
        return f"<JobPosition title={self.title} critical={self.is_safety_critical}>"

class Employee(BaseAuditModel):
    """
    员工花名册，实现人事实体与系统账号解耦 (docs/04)
    """
    __tablename__ = "hr_employees"

    employee_no = Column(String(50), unique=True, nullable=False, index=True) # 工号，如 BR-2026-001
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    department_id = Column(String(36), ForeignKey("hr_departments.id", ondelete="RESTRICT"), nullable=False)
    job_id = Column(String(36), ForeignKey("hr_job_positions.id", ondelete="RESTRICT"), nullable=True)
    manager_id = Column(String(36), ForeignKey("hr_employees.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False, index=True)
    hire_date = Column(DateTime, nullable=True)
    user_id = Column(String(36), ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True, unique=True) # 绑定的登录账号
    avatar_url = Column(String(500), nullable=True) # 员工电子档案头像存储路径

    department = relationship("Department", back_populates="employees")
    job_position = relationship("JobPosition", back_populates="employees")
    user = relationship("User", lazy="selectin", foreign_keys=[user_id])
    certifications = relationship("EmployeeCertification", back_populates="employee", cascade="all, delete-orphan", lazy="selectin")
    trainings = relationship("EmployeeTraining", back_populates="employee", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Employee no={self.employee_no} name={self.name} status={self.status}>"


class EmployeeCertification(BaseAuditModel):
    """
    ISO / KBA 资质与上岗证书矩阵 (Competency Matrix - docs/04)
    """
    __tablename__ = "hr_employee_certifications"

    employee_id = Column(String(36), ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cert_name = Column(String(150), nullable=False)                         # 证书名称 (如: KBA CoP 主任审核员资质)
    cert_type = Column(String(50), nullable=False, index=True)              # 证书类型编码 (如: KBA_COP_AUDITOR)
    cert_no = Column(String(100), nullable=False, index=True)               # 证书统一编号
    issuing_authority = Column(String(100), nullable=False)                 # 颁发机构 (如: TÜV SÜD / DEKRA)
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)              # 证书到期日
    is_valid = Column(Boolean, default=True, nullable=False)                # 手工失效标记
    attachment_url = Column(String(255), nullable=True)                     # 凭据附件存储路径

    employee = relationship("Employee", back_populates="certifications")

    @property
    def is_expired(self) -> bool:
        """检查证书是否物理过期"""
        now = datetime.now(timezone.utc)
        target = self.expiry_date
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        return now > target

    @property
    def days_to_expire(self) -> int:
        """距离到期剩余天数"""
        now = datetime.now(timezone.utc)
        target = self.expiry_date
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        return (target - now).days

    def __repr__(self):
        return f"<Certification no={self.cert_no} name={self.cert_name}>"

class EmployeeTraining(BaseAuditModel):
    """
    培训履历与有效性评价记录 (符合 ISO 9001 7.2 及 KBA 要求 - docs/04)
    """
    __tablename__ = "hr_employee_trainings"

    employee_id = Column(String(36), ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    training_topic = Column(String(150), nullable=False)
    training_date = Column(DateTime, nullable=False)
    hours = Column(Float, default=1.0, nullable=False)
    trainer = Column(String(100), nullable=True)
    score = Column(Float, nullable=True)
    is_passed = Column(Boolean, default=True, nullable=False)
    effectiveness_evaluation = Column(Text, nullable=True) # ISO 9001 过程评价（上岗实操/盲测验证合格）

    employee = relationship("Employee", back_populates="trainings")

    def __repr__(self):
        return f"<Training topic={self.training_topic} passed={self.is_passed}>"
