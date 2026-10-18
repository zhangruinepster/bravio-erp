from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import BackupType

class BackupRecordResponse(BaseModel):
    id: str
    backup_name: str
    backup_type: BackupType
    file_size_bytes: int
    sha256_checksum: str
    notes: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CreateBackupRequest(BaseModel):
    notes: Optional[str] = "管理员控制台手动快照"
