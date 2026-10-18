from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import PartnerType

class PartnerBase(BaseModel):
    partner_code: str
    name: str
    partner_type: PartnerType = PartnerType.SUPPLIER
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_oem_certified: bool = False
    payment_terms_days: int = 60
    shipping_address: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[PartnerType] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_oem_certified: Optional[bool] = None
    payment_terms_days: Optional[int] = None
    shipping_address: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class PartnerResponse(PartnerBase):
    id: str
    api_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

