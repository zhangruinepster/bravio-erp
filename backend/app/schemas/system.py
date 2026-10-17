from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    uptime_seconds: float
    timestamp: datetime

class DevLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    module: str
    line: int
    function: str
    extra: Dict[str, Any] = {}

class DevLogsResponse(BaseModel):
    total_logs_in_memory: int
    returned_count: int
    logs: List[DevLogEntry]
