from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import BomComponentCategory

class BomItemBase(BaseModel):
    part_number: str
    part_name: str
    category: BomComponentCategory = BomComponentCategory.PART
    quantity: float = 1.0
    unit: str = "PCS"
    reference_designator: Optional[str] = None
    is_safety_critical: bool = False

class BomItemCreate(BomItemBase):
    pass

class BomItemResponse(BomItemBase):
    id: str
    bom_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PackagingHierarchyBase(BaseModel):
    pieces_per_box: int = 2
    boxes_per_carton: int = 20
    cartons_per_pallet: int = 24
    box_spec: Optional[str] = "220x150x80mm"
    carton_spec: Optional[str] = "620x450x340mm"
    notes: Optional[str] = None

class PackagingHierarchyResponse(PackagingHierarchyBase):
    id: str
    bom_id: str
    model_config = ConfigDict(from_attributes=True)

class BomCreate(BaseModel):
    product_id: str
    version: str = "V1.0"
    description: Optional[str] = None
    items: List[BomItemCreate] = []
    packaging: Optional[PackagingHierarchyBase] = None

class BomResponse(BaseModel):
    id: str
    product_id: str
    version: str
    is_active: bool
    description: Optional[str]
    items: List[BomItemResponse] = []
    packaging: Optional[PackagingHierarchyResponse] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
