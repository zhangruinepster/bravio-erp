import enum
from sqlalchemy import Column, String, Boolean, Table, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseAuditModel

class DataScope(str, enum.Enum):
    """
    符合 docs/03 规范的数据范围权限控制 (ABAC/Data Scopes)
    """
    ALL = "ALL"                         # 全集团所有数据 (如质量总监/超级管理员)
    DEPT_AND_CHILD = "DEPT_AND_CHILD"   # 所在部门及所有下级部门
    DEPT_ONLY = "DEPT_ONLY"             # 仅限本直属部门
    SELF_ONLY = "SELF_ONLY"             # 仅限本人创建或绑定的记录

# 用户与角色多对多关联中间表
user_roles = Table(
    "sys_user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
)

# 角色与权限多对多关联中间表
role_permissions = Table(
    "sys_role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("sys_permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(BaseAuditModel):
    """
    功能权限项，遵循 docs/03 命名空间体系：module.resource.action
    例如: hr.employee.create, hr.cert.approve, kba.cop.audit
    """
    __tablename__ = "sys_permissions"

    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False, index=True) # hr, rbac, qms, kba, wms 等
    description = Column(String(255), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions", lazy="selectin")

    def __repr__(self):
        return f"<Permission code={self.code} name={self.name}>"

class Role(BaseAuditModel):
    """
    系统角色，支持开箱即用与自定义角色，携带默认数据范围
    """
    __tablename__ = "sys_roles"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    data_scope = Column(SQLEnum(DataScope), default=DataScope.DEPT_ONLY, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False) # 系统内置保留角色不可随意物理删除

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="selectin")
    users = relationship("User", secondary=user_roles, back_populates="roles", lazy="selectin")

    def __repr__(self):
        return f"<Role code={self.code} name={self.name} data_scope={self.data_scope}>"
