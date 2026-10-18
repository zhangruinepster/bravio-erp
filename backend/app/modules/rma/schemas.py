from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import RmaStatus

class RmaCreateRequest(BaseModel):
    customer_name: str
    returned_sn: str
    returned_box_code: Optional[str] = None
    claim_reason: str

class RmaInspectRequest(BaseModel):
    replacement_sn: Optional[str] = None
    inspector_notes: Optional[str] = None

class RmaResponse(BaseModel):
    id: str
    rma_number: str
    customer_name: str
    returned_sn: str
    returned_box_code: Optional[str]
    claim_reason: str
    is_fraud_detected: bool
    fraud_reason: Optional[str]
    sample_location_matched: Optional[str]
    replacement_sn: Optional[str]
    status: RmaStatus
    inspector_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
