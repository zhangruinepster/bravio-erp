from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import PackagingUnit, PackagingUnitLevel, PackagingUnitStatus
from .schemas import PackagingPackRequest, DeconstructBoxRequest

class WmsService:
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[PackagingUnit]:
        stmt = select(PackagingUnit).where(PackagingUnit.unit_code == code, PackagingUnit.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_all_by_level(db: AsyncSession, level: Optional[PackagingUnitLevel] = None) -> List[PackagingUnit]:
        stmt = select(PackagingUnit).where(PackagingUnit.is_deleted == False)
        if level:
            stmt = stmt.where(PackagingUnit.level == level)
        stmt = stmt.order_by(PackagingUnit.created_at.desc())
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def pack_units(db: AsyncSession, req: PackagingPackRequest, user_id: str) -> PackagingUnit:
        """向上聚合封装 (如把多个 BOX 封装入一个 CARTON)"""
        parent = await WmsService.get_by_code(db, req.parent_code)
        if not parent:
            parent = PackagingUnit(
                unit_code=req.parent_code,
                level=req.parent_level,
                status=PackagingUnitStatus.IN_WAREHOUSE,
                bravio_id=req.bravio_id,
                warehouse_location=req.warehouse_location,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(parent)
            await db.flush()

        for c_code in req.child_codes:
            child = await WmsService.get_by_code(db, c_code)
            if not child:
                # 自动创建子层节点
                child_level_map = {
                    PackagingUnitLevel.BOX: PackagingUnitLevel.SN,
                    PackagingUnitLevel.CARTON: PackagingUnitLevel.BOX,
                    PackagingUnitLevel.PALLET: PackagingUnitLevel.CARTON
                }
                c_level = child_level_map.get(req.parent_level, PackagingUnitLevel.SN)
                child = PackagingUnit(
                    unit_code=c_code,
                    level=c_level,
                    parent_id=parent.id,
                    status=PackagingUnitStatus.PACKED,
                    bravio_id=req.bravio_id,
                    created_by_id=user_id,
                    updated_by_id=user_id
                )
                db.add(child)
            else:
                child.parent_id = parent.id
                child.status = PackagingUnitStatus.PACKED
                child.updated_by_id = user_id

        await db.commit()
        await db.refresh(parent)
        return parent

    @staticmethod
    async def deconstruct_carton(db: AsyncSession, req: DeconstructBoxRequest, user_id: str) -> PackagingUnit:
        """德国仓 IQC 抽检拆解：将彩盒拆离外箱，原箱降级为 PARTIAL_OPENED，彩盒归入散件池"""
        carton = await WmsService.get_by_code(db, req.carton_code)
        if not carton:
            raise HTTPException(status_code=404, detail="外箱单元不存在")

        box = await WmsService.get_by_code(db, req.box_code_to_remove)
        if not box:
            raise HTTPException(status_code=404, detail="彩盒单元不存在")

        # 状态解构与降级
        box.parent_id = None
        box.status = PackagingUnitStatus.LOOSE_SPARE_POOL
        box.notes = f"抽检拆解: {req.reason}"
        box.updated_by_id = user_id

        carton.status = PackagingUnitStatus.PARTIAL_OPENED
        carton.notes = f"已解包抽检，变为余箱 (Partial)"
        carton.updated_by_id = user_id

        await db.commit()
        await db.refresh(carton)
        return carton
