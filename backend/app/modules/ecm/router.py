from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import EcoCreate, EcoApproveRequest, EcoResponse
from .service import EcmService

router = APIRouter(prefix="/ecm", tags=["工程变更管理 (ECM / ECO)"])

@router.get("", response_model=List[EcoResponse], summary="查询工程变更指令列表")
async def list_ecos(
    product_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await EcmService.get_all(db, product_id)

@router.get("/{eco_id}", response_model=EcoResponse, summary="查询 ECO 详情")
async def get_eco(
    eco_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    eco = await EcmService.get_by_id(db, eco_id)
    if not eco:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="工程变更不存在")
    return eco

@router.post("", response_model=EcoResponse, status_code=status.HTTP_201_CREATED, summary="发起工程变更申请 (ECR -> ECO)")
async def create_eco(
    data: EcoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await EcmService.create(db, data, current_user.id)

@router.post("/{eco_id}/review", response_model=EcoResponse, summary="工程变更跨部门会签评审 (批准/驳回)")
async def review_eco(
    eco_id: str,
    req: EcoApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reviewer_name = current_user.full_name or current_user.username
    return await EcmService.review(db, eco_id, req, reviewer_name, current_user.id)

@router.post("/{eco_id}/release", response_model=EcoResponse, summary="生效并发布变更通知 (ECN Release)")
async def release_eco(
    eco_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await EcmService.release(db, eco_id, current_user.id)
