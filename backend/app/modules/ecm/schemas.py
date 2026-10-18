from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import EcoStatus, EcoChangeType

class EcoBase(BaseModel):
    eco_number: str
    product_id: str
    title: str
    change_type: EcoChangeType = EcoChangeType.DESIGN
    reason: str
    affects_drawings: bool = True
    affects_bom: bool = False
    affects_kba_homologation: bool = False
    kba_eval_notes: Optional[str] = None
    status: EcoStatus = EcoStatus.DRAFT

class EcoCreate(BaseModel):
    product_id: str
    title: str
    change_type: EcoChangeType = EcoChangeType.DESIGN
    reason: str
    affects_drawings: bool = True
    affects_bom: bool = False
    affects_kba_homologation: bool = False
    kba_eval_notes: Optional[str] = None

class EcoApproveRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None

class EcoResponse(EcoBase):
    id: str
    approver_name: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
