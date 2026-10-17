from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "operator"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
