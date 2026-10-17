import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class BaseAuditModel(Base):
    """
    符合 Bravio ERP 规范的企业级通用审计抽象基类
    包含：UUID主键、创建时间、更新时间、软删除标记、乐观锁版本号
    """
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    created_by_id = Column(String(36), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    updated_by_id = Column(String(36), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    version_id = Column(Integer, default=1, nullable=False)  # 乐观锁控制
