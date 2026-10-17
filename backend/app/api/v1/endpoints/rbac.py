from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, require_permissions
from app.models.user import User
from app.models.rbac import Role, Permission, DataScope, user_roles
from app.schemas.rbac import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse

router = APIRouter()

@router.get("/permissions", response_model=List[PermissionResponse], summary="获取系统所有注册的功能权限项")
async def list_permissions(
    module: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Permission).where(Permission.is_deleted == False)
    if module:
        stmt = stmt.where(Permission.module == module)
    stmt = stmt.order_by(Permission.module.asc(), Permission.code.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/roles", response_model=List[RoleResponse], summary="获取系统角色矩阵及权限关联")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Role).options(selectinload(Role.permissions)).where(Role.is_deleted == False).order_by(Role.code.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="创建自定义角色并关联权限")
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("system.role.create"))
):
    exist = (await db.execute(select(Role).where(Role.code == role_in.code, Role.is_deleted == False))).scalar_one_or_none()
    if exist:
        raise HTTPException(status_code=400, detail=f"角色代码 '{role_in.code}' 已存在")

    role = Role(
        code=role_in.code,
        name=role_in.name,
        description=role_in.description,
        data_scope=role_in.data_scope,
        is_system=False,
        created_by_id=current_user.id
    )

    if role_in.permission_ids:
        perms_stmt = select(Permission).where(Permission.id.in_(role_in.permission_ids), Permission.is_deleted == False)
        perms = (await db.execute(perms_stmt)).scalars().all()
        role.permissions = list(perms)

    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role
