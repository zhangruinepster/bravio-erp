from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import PairingStatus

class LaserCodeBase(BaseModel):
    serial_number: str
    product_id: str
    bravio_id: str
    revision: str = "A"
    year_week: str
    sequence_no: str
    color_temp_bin: str = "6000K"
    flux_bin: str = "1200LM"
    voltage_bin: str = "12V"
    raw_bin_code: str
    is_paired: bool = False
    paired_box_id: Optional[str] = None
    station_id: str = "STATION-PACK-01"

class LaserCodeCreate(BaseModel):
    product_id: str
    bravio_id: str
    revision: str = "A"
    sequence_int: int = 1
    color_temp_bin: str = "6000K"
    flux_bin: str = "1200LM"
    voltage_bin: str = "12V"
    station_id: str = "STATION-PACK-01"

class LaserCodeResponse(LaserCodeBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PairingCheckRequest(BaseModel):
    box_barcode: str
    sn_first: str
    sn_second: str
    station_id: Optional[str] = "STATION-PACK-01"

class PairingCheckResponse(BaseModel):
    is_pass: bool
    status: PairingStatus
    box_barcode: str
    message: str
    sn_first: str
    sn_second: str
    first_bin: str
    second_bin: str
