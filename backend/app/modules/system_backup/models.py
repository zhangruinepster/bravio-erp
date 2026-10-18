import enum
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, Text
from app.models.base import BaseAuditModel

class BackupType(str, enum.Enum):
    MANUAL = "MANUAL"       # 管理员手动触发
    SCHEDULED = "SCHEDULED" # 定时快照守护进程

class BackupRecord(BaseAuditModel):
    """
    数据库备份与灾备恢复快照档案 (docs/05)
    """
    __tablename__ = "backup_records"

    backup_name = Column(String(100), unique=True, nullable=False, index=True)
    backup_type = Column(SQLEnum(BackupType), default=BackupType.MANUAL, nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    sha256_checksum = Column(String(64), nullable=False) # 校验防篡改
    notes = Column(Text, nullable=True)
