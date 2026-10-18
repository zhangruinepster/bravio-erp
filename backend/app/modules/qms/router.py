from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import InspectionCreate, InspectionResponse, EightDCreate, EightDUpdate, EightDResponse
from .service import QmsService

router = APIRouter(prefix="/qms", tags=["质量管理与 8D 失效攻关 (QMS)"])

@router.get("/inspections", response_model=List[InspectionResponse], summary="查询质量检验单 (IQC/IPQC/FQC)")
async def list_inspections(
    product_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await QmsService.list_inspections(db, product_id)

@router.post("/inspections", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED, summary="录入质检报告单")
async def create_inspection(
    data: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    name = current_user.full_name or current_user.username
    return await QmsService.create_inspection(db, data, name, current_user.id)

@router.get("/incidents-8d", response_model=List[EightDResponse], summary="查询 8D 质量攻关工单列表")
async def list_eight_d(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await QmsService.list_eight_d(db)

@router.post("/incidents-8d", response_model=EightDResponse, status_code=status.HTTP_201_CREATED, summary="发起 8D 质量异常攻关")
async def create_eight_d(
    data: EightDCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await QmsService.create_eight_d(db, data, current_user.id)

@router.put("/incidents-8d/{incident_id}", response_model=EightDResponse, summary="推进 8D 步骤 (D3围堵/D4根本原因/D5纠正/D7预防闭环)")
async def update_eight_d(
    incident_id: str,
    data: EightDUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await QmsService.update_eight_d(db, incident_id, data, current_user.id)
