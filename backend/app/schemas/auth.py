from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., description="登录账号 / 用户名或邮箱")
    password: str = Field(..., description="登录密码")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserBrief(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_superuser: bool

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: TokenResponse
    user: UserBrief
