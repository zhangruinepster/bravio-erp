from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import ProductLifecycleStatus

class ProductBase(BaseModel):
    bravio_id: str
    product_name: str
    current_revision: str = "A"
    category: str = "HEADLIGHT"
    primary_image_url: Optional[str] = None
    technical_spec_pdf_url: Optional[str] = None
    is_certified: bool = True
    kba_approval_number: Optional[str] = None
    homologation_authority: str = "KBA-Flensburg"
    iso_classification: str = "SAFETY_RELEVANT"
    is_serialized: bool = True
    standard_warranty_months: int = 24
    lifecycle_status: ProductLifecycleStatus = ProductLifecycleStatus.PROJECT_KICKOFF
    current_phase_gate: int = 1
    notes: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    current_revision: Optional[str] = None
    category: Optional[str] = None
    primary_image_url: Optional[str] = None
    technical_spec_pdf_url: Optional[str] = None
    is_certified: Optional[bool] = None
    kba_approval_number: Optional[str] = None
    homologation_authority: Optional[str] = None
    iso_classification: Optional[str] = None
    is_serialized: Optional[bool] = None
    standard_warranty_months: Optional[int] = None
    lifecycle_status: Optional[ProductLifecycleStatus] = None
    current_phase_gate: Optional[int] = None
    notes: Optional[str] = None


class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
