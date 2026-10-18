from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import IsoDocLevel, DocStatus

class DocumentBase(BaseModel):
    doc_number: str
    title: str
    doc_level: IsoDocLevel = IsoDocLevel.LEVEL_3_WI
    version: str = "V1.0"
    department_scope: str = "ALL"
    file_url: Optional[str] = None
    watermark_text: Optional[str] = "Bravio Confidential"
    status: DocStatus = DocStatus.APPROVED_EFFECTIVE
    summary: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
