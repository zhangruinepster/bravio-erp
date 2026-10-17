from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login-form",
    auto_error=False
)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证凭据无效或已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id, User.is_deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前账号已被停用，请联系系统管理员"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作权限不足：需要系统管理员权限"
        )
    return current_user

def require_permissions(*required_perms: str):
    """
    细粒度 RBAC 权限守卫依赖项 (docs/03)
    支持多权限校验，超级管理员或拥有对应 permission code 的用户方可放行
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser or current_user.role == "admin":
            return current_user

        # 聚合用户持有的所有权限代码
        user_perm_codes = set()
        for role in getattr(current_user, "roles", []):
            for perm in getattr(role, "permissions", []):
                user_perm_codes.add(perm.code)

        missing = [p for p in required_perms if p not in user_perm_codes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"操作权限不足：缺少必要的功能权限 [{', '.join(missing)}]"
            )
        return current_user

    return permission_checker

def require_roles(*required_role_codes: str):
    """
    角色守卫依赖项
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser or current_user.role == "admin":
            return current_user

        user_role_codes = {r.code for r in getattr(current_user, "roles", [])}
        # 兼容旧 role 字符串
        if current_user.role:
            user_role_codes.add(current_user.role)

        if not any(r in user_role_codes for r in required_role_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"操作权限不足：需要角色 [{', '.join(required_role_codes)}]"
            )
        return current_user

    return role_checker

