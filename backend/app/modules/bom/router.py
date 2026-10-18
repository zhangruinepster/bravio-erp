from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import BomCreate, BomResponse
from .service import BomService

router = APIRouter(prefix="/boms", tags=["物料清单与出货包装层级 (BOM)"])

@router.get("/product/{product_id}", response_model=List[BomResponse], summary="查询产品的 BOM 版本列表")
async def get_product_boms(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await BomService.get_by_product_id(db, product_id)

@router.get("/{bom_id}", response_model=BomResponse, summary="查询 BOM 详情与包含物料")
async def get_bom(
    bom_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bom = await BomService.get_by_id(db, bom_id)
    if not bom:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="BOM 不存在")
    return bom

@router.post("", response_model=BomResponse, status_code=status.HTTP_201_CREATED, summary="定义新版本 BOM 与包装层级")
async def create_bom(
    data: BomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await BomService.create(db, data, current_user.id)
