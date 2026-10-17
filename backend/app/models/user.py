from sqlalchemy import Column, String, Boolean, DateTime
from app.models.base import BaseAuditModel

class User(BaseAuditModel):
    __tablename__ = "sys_users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="operator", nullable=False)  # admin, manager, operator, auditor
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<User username={self.username} role={self.role}>"
