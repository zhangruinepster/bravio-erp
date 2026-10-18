from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import B2bWorkOrderStatus

class B2bWorkOrderCreate(BaseModel):
    partner_id: str
    product_id: str
    bravio_id: str
    planned_quantity: int = 500
    notes: Optional[str] = None

class B2bWorkOrderResponse(BaseModel):
    id: str
    order_number: str
    partner_id: str
    product_id: str
    bravio_id: str
    planned_quantity: int
    sn_range_start: Optional[str]
    sn_range_end: Optional[str]
    status: B2bWorkOrderStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class B2bFqcUploadRequest(BaseModel):
    order_number: str
    inspected_quantity: int
    pass_count: int
    dimension_verified: bool = True
    optical_verified: bool = True
