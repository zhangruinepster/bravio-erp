from sqlalchemy import Column, String, Text, DateTime
from app.models.base import BaseAuditModel, utc_now

class AuditLog(BaseAuditModel):
    __tablename__ = "sys_audit_logs"

    request_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)   # e.g., AUTH_LOGIN, USER_UPDATE, SYSTEM_STARTUP
    module = Column(String(50), nullable=False)   # e.g., auth, rbac, hr, system
    client_ip = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)         # JSON/Text details
    status = Column(String(20), default="SUCCESS") # SUCCESS, FAILED
