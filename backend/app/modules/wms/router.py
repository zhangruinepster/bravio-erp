from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .models import PackagingUnitLevel
from .schemas import PackagingPackRequest, DeconstructBoxRequest, PackagingUnitNode
from .service import WmsService

router = APIRouter(prefix="/wms", tags=["四级包装聚合树与仓储中心 (WMS)"])

@router.get("/units", response_model=List[PackagingUnitNode], summary="查询包装聚合单元列表 (SN/BOX/CTN/PLT)")
async def list_units(
    level: Optional[PackagingUnitLevel] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    units = await WmsService.get_all_by_level(db, level)
    res = []
    for u in units:
        res.append(PackagingUnitNode(
            id=u.id,
            unit_code=u.unit_code,
            level=u.level,
            status=u.status,
            parent_id=u.parent_id,
            warehouse_location=u.warehouse_location,
            children_count=len(u.children) if u.children else 0,
            children=[],
            created_at=u.created_at
        ))
    return res

@router.post("/pack", summary="四级包装聚合打包入库")
async def pack_units(
    req: PackagingPackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parent = await WmsService.pack_units(db, req, current_user.id)
    return {
        "success": True,
        "message": f"成功聚合包装单元 [{parent.unit_code}] ({parent.level})",
        "parent_code": parent.unit_code,
        "status": parent.status
    }

@router.post("/deconstruct-sample", summary="德国仓 IQC 抽检解包与散件池归集")
async def deconstruct_carton(
    req: DeconstructBoxRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    carton = await WmsService.deconstruct_carton(db, req, current_user.id)
    return {
        "success": True,
        "message": f"外箱 [{carton.unit_code}] 抽检解构成功，已降级为 PARTIAL_OPENED，彩盒已移入 LOOSE_SPARE_POOL",
        "carton_status": carton.status
    }
