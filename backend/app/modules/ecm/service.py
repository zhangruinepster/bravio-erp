import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import EngineeringChangeOrder, EcoStatus
from .schemas import EcoCreate, EcoApproveRequest

class EcmService:
    @staticmethod
    async def get_all(db: AsyncSession, product_id: Optional[str] = None) -> List[EngineeringChangeOrder]:
        stmt = select(EngineeringChangeOrder).where(EngineeringChangeOrder.is_deleted == False).order_by(EngineeringChangeOrder.created_at.desc())
        if product_id:
            stmt = stmt.where(EngineeringChangeOrder.product_id == product_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, eco_id: str) -> Optional[EngineeringChangeOrder]:
        stmt = select(EngineeringChangeOrder).where(EngineeringChangeOrder.id == eco_id, EngineeringChangeOrder.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: EcoCreate, user_id: str) -> EngineeringChangeOrder:
        eco_num = f"ECO-{time.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        eco = EngineeringChangeOrder(
            eco_number=eco_num,
            **data.model_dump(),
            status=EcoStatus.UNDER_REVIEW,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(eco)
        await db.commit()
        await db.refresh(eco)
        return eco

    @staticmethod
    async def review(db: AsyncSession, eco_id: str, req: EcoApproveRequest, reviewer_name: str, user_id: str) -> EngineeringChangeOrder:
        eco = await EcmService.get_by_id(db, eco_id)
        if not eco:
            raise HTTPException(status_code=404, detail="工程变更指令不存在")

        eco.status = EcoStatus.APPROVED if req.approved else EcoStatus.REJECTED
        eco.approver_name = reviewer_name
        eco.approval_notes = req.notes
        eco.updated_by_id = user_id
        await db.commit()
        await db.refresh(eco)
        return eco

    @staticmethod
    async def release(db: AsyncSession, eco_id: str, user_id: str) -> EngineeringChangeOrder:
        eco = await EcmService.get_by_id(db, eco_id)
        if not eco:
            raise HTTPException(status_code=404, detail="工程变更指令不存在")
        if eco.status != EcoStatus.APPROVED:
            raise HTTPException(status_code=400, detail="仅已批准状态的 ECO 方可发布实施 (ECN)")

        eco.status = EcoStatus.RELEASED
        eco.updated_by_id = user_id
        await db.commit()
        await db.refresh(eco)
        return eco
