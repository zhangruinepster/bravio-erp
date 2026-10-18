from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import InspectionType, InspectionResult, EightDStatus

class InspectionCreate(BaseModel):
    inspection_type: InspectionType = InspectionType.FQC
    product_id: str
    bravio_id: str
    batch_number: str
    sample_size: int = 5
    defect_count: int = 0
    dimension_check_passed: bool = True
    optical_check_passed: bool = True
    kba_cop_compliant: bool = True
    overall_result: InspectionResult = InspectionResult.PASS
    notes: Optional[str] = None

class InspectionResponse(InspectionCreate):
    id: str
    sheet_number: str
    inspector_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EightDCreate(BaseModel):
    title: str
    product_id: str
    source: str = "CUSTOMER_COMPLAINT"
    d1_team_leader: Optional[str] = None
    d2_problem_description: str
    d3_interim_containment: Optional[str] = None

class EightDUpdate(BaseModel):
    status: Optional[EightDStatus] = None
    d3_interim_containment: Optional[str] = None
    d4_root_cause: Optional[str] = None
    d5_permanent_corrective: Optional[str] = None
    d7_prevent_recurrence: Optional[str] = None
    closure_notes: Optional[str] = None

class EightDResponse(BaseModel):
    id: str
    incident_number: str
    title: str
    product_id: str
    source: str
    status: EightDStatus
    d1_team_leader: Optional[str]
    d2_problem_description: str
    d3_interim_containment: Optional[str]
    d4_root_cause: Optional[str]
    d5_permanent_corrective: Optional[str]
    d7_prevent_recurrence: Optional[str]
    closure_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
