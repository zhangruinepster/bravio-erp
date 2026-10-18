from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import LaserCodeCreate, LaserCodeResponse, PairingCheckRequest, PairingCheckResponse
from .service import TraceabilityService

router = APIRouter(prefix="/traceability", tags=["32位激光刻码与一盒双支配对防呆 (Traceability)"])

@router.post("/laser-codes", response_model=LaserCodeResponse, status_code=status.HTTP_201_CREATED, summary="烧录/刻印单品 32 位激光微距序列号")
async def create_laser_code(
    data: LaserCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await TraceabilityService.create_laser_code(db, data, current_user.id)

@router.get("/laser-codes/{sn}", response_model=LaserCodeResponse, summary="查询 32 位单品档案与 Binning 详细信息")
async def get_laser_code(
    sn: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code = await TraceabilityService.get_by_sn(db, sn)
    if not code:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="激光序列号不存在")
    return code

@router.post("/pairing/check-box", response_model=PairingCheckResponse, summary="包装工位一盒双支 Binning 强制防呆核对 (Poka-Yoke)")
async def check_pairing(
    req: PairingCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    operator_name = current_user.full_name or current_user.username
    return await TraceabilityService.check_and_pair_box(db, req, operator_name, current_user.id)
