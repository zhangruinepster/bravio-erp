from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import ProductCreate, ProductUpdate, ProductResponse
from .service import ProductService
from .models import ProductLifecycleStatus

router = APIRouter(prefix="/products", tags=["产品研发与主数据管理 (Product Master)"])

@router.get("", response_model=List[ProductResponse], summary="查询产品主数据列表")
async def list_products(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await ProductService.get_all(db, category)

@router.get("/{product_id}", response_model=ProductResponse, summary="获取产品详情")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prod = await ProductService.get_by_id(db, product_id)
    if not prod:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="产品档案不存在")
    return prod

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="定义新产品主数据")
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await ProductService.create(db, data, current_user.id)

@router.put("/{product_id}", response_model=ProductResponse, summary="修改产品主数据")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await ProductService.update(db, product_id, data, current_user.id)

@router.post("/{product_id}/advance-lifecycle", response_model=ProductResponse, summary="推进 APQP 阶段门生命周期")
async def advance_lifecycle(
    product_id: str,
    target_status: ProductLifecycleStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await ProductService.advance_lifecycle(db, product_id, target_status, current_user.id)
