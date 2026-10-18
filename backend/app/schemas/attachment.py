from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AttachmentBase(BaseModel):
    file_name: str
    content_type: str
    file_size: int
    file_url: str
    sha256_hash: str
    res_model: str
    res_id: Optional[str] = None
    description: Optional[str] = None

class AttachmentResponse(AttachmentBase):
    id: str
    stored_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AttachmentStatsResponse(BaseModel):
    total_count: int
    total_size_bytes: int
    total_size_mb: float
    model_breakdown: Dict[str, int]
    model_config = ConfigDict(protected_namespaces=())
