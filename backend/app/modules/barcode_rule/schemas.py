from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import BarcodeLevel

class BarcodeRuleBase(BaseModel):
    name: str
    level: BarcodeLevel
    template: str
    regex_pattern: str
    is_default: bool = False
    description: Optional[str] = None

class BarcodeRuleCreate(BarcodeRuleBase):
    pass

class BarcodeRuleResponse(BarcodeRuleBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BarcodeGenerateRequest(BaseModel):
    level: BarcodeLevel
    bravio_id: str
    revision: str = "A"
    year_week: Optional[str] = None  # 如 "2642"
    sequence: int = 1
    binning: Optional[str] = "6000K-1200LM-12V"

class BarcodeParseRequest(BaseModel):
    barcode: str

class BarcodeParseResponse(BaseModel):
    raw_barcode: str
    level: str
    is_valid: bool
    parsed_fields: Dict[str, Any] = {}
