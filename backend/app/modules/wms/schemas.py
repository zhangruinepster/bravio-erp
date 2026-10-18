from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import PackagingUnitLevel, PackagingUnitStatus

class PackagingUnitBase(BaseModel):
    unit_code: str
    level: PackagingUnitLevel
    parent_id: Optional[str] = None
    status: PackagingUnitStatus = PackagingUnitStatus.PACKED
    product_id: Optional[str] = None
    bravio_id: Optional[str] = None
    warehouse_location: Optional[str] = "MUC-WH-A-01"
    notes: Optional[str] = None

class PackagingUnitCreate(PackagingUnitBase):
    pass

class PackagingUnitNode(BaseModel):
    id: str
    unit_code: str
    level: PackagingUnitLevel
    status: PackagingUnitStatus
    parent_id: Optional[str]
    warehouse_location: Optional[str]
    children_count: int = 0
    children: List['PackagingUnitNode'] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PackagingPackRequest(BaseModel):
    parent_code: str
    parent_level: PackagingUnitLevel
    child_codes: List[str]
    bravio_id: Optional[str] = None
    warehouse_location: Optional[str] = "MUC-WH-A-01"

class DeconstructBoxRequest(BaseModel):
    carton_code: str
    box_code_to_remove: str
    reason: str = "德国仓 IQC 抽检留样拆除"
