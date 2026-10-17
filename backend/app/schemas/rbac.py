from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.rbac import DataScope

class PermissionBase(BaseModel):
    code: str
    name: str
    module: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    data_scope: DataScope = DataScope.DEPT_ONLY

class RoleCreate(RoleBase):
    permission_ids: Optional[List[str]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[DataScope] = None
    permission_ids: Optional[List[str]] = None

class RoleResponse(RoleBase):
    id: str
    is_system: bool
    created_at: datetime
    permissions: List[PermissionResponse] = []
    model_config = ConfigDict(from_attributes=True)
