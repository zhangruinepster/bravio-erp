from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import B2bWorkOrderCreate, B2bWorkOrderResponse, B2bFqcUploadRequest
from .service import B2bService

router = APIRouter(prefix="/b2b", tags=["外部代工厂与供应链 M2M 协同 (B2B API - docs/16)"])

@router.get("/work-orders", response_model=List[B2bWorkOrderResponse], summary="查询外部外协代工单列表")
async def list_orders(
    partner_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await B2bService.list_orders(db, partner_id)

@router.post("/work-orders", response_model=B2bWorkOrderResponse, status_code=status.HTTP_201_CREATED, summary="下达代工任务与预分配条码段")
async def create_order(
    data: B2bWorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await B2bService.create_order(db, data, current_user.id)

@router.post("/fqc-upload", response_model=B2bWorkOrderResponse, summary="代工厂出厂质检数据 M2M 上传通道")
async def upload_fqc(
    req: B2bFqcUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await B2bService.upload_fqc(db, req, current_user.id)
