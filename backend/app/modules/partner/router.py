from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .models import PartnerType
from .schemas import PartnerCreate, PartnerUpdate, PartnerResponse
from .service import PartnerService

router = APIRouter(prefix="/partners", tags=["商业伙伴管理 (供应商与客户 - docs/17)"])

@router.get("", response_model=List[PartnerResponse], summary="查询商业伙伴列表 (供应商/客户)")
async def list_partners(
    partner_type: Optional[PartnerType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PartnerService.list_partners(db, partner_type)

@router.get("/{partner_id}", response_model=PartnerResponse, summary="查询单个商业伙伴详情")
async def get_partner(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = await PartnerService.get_by_id(db, partner_id)
    if not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="商业伙伴档案不存在")
    return p

@router.post("", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED, summary="建立新商业伙伴档案 (自动分配集成 Token)")
async def create_partner(
    data: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PartnerService.create(db, data, current_user.id)

@router.put("/{partner_id}", response_model=PartnerResponse, summary="修改商业伙伴档案")
async def update_partner(
    partner_id: str,
    data: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PartnerService.update(db, partner_id, data, current_user.id)

