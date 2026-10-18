from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import RmaCreateRequest, RmaInspectRequest, RmaResponse
from .service import RmaService

router = APIRouter(prefix="/rma", tags=["售后逆向风控与 RMA 验真 (RMA)"])

@router.get("", response_model=List[RmaResponse], summary="查询售后 RMA 工单列表")
async def list_rmas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await RmaService.get_all(db)

@router.post("", response_model=RmaResponse, status_code=status.HTTP_201_CREATED, summary="提交售后退回申请并执行自动风控反欺诈验真")
async def submit_rma(
    req: RmaCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await RmaService.submit_rma(db, req, current_user.id)

@router.post("/{rma_id}/complete", response_model=RmaResponse, summary="质保判定通过并完成同 Bin 备品补发出库")
async def complete_rma(
    rma_id: str,
    req: RmaInspectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await RmaService.approve_and_dispatch_replacement(db, rma_id, req, current_user.id)
