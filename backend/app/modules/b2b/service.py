import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import B2bWorkOrder, B2bWorkOrderStatus
from .schemas import B2bWorkOrderCreate, B2bFqcUploadRequest

class B2bService:
    @staticmethod
    async def list_orders(db: AsyncSession, partner_id: Optional[str] = None) -> List[B2bWorkOrder]:
        stmt = select(B2bWorkOrder).where(B2bWorkOrder.is_deleted == False).order_by(B2bWorkOrder.created_at.desc())
        if partner_id:
            stmt = stmt.where(B2bWorkOrder.partner_id == partner_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_order(db: AsyncSession, data: B2bWorkOrderCreate, user_id: str) -> B2bWorkOrder:
        order_num = f"WO-{time.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        
        # 预分配条码段
        yw = time.strftime('%y%U')
        sn_start = f"{data.bravio_id[:5]:0>5}A{yw}00000001DEFAULTBIN00"
        sn_end = f"{data.bravio_id[:5]:0>5}A{yw}{data.planned_quantity:08d}DEFAULTBIN00"

        order = B2bWorkOrder(
            order_number=order_num,
            sn_range_start=sn_start,
            sn_range_end=sn_end,
            status=B2bWorkOrderStatus.RELEASED,
            **data.model_dump(),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def upload_fqc(db: AsyncSession, req: B2bFqcUploadRequest, user_id: str) -> B2bWorkOrder:
        stmt = select(B2bWorkOrder).where(B2bWorkOrder.order_number == req.order_number, B2bWorkOrder.is_deleted == False)
        order = (await db.execute(stmt)).scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="外协代工单不存在")

        order.status = B2bWorkOrderStatus.FQC_SUBMITTED
        order.notes = f"代工厂已上传出厂 FQC (合格: {req.pass_count}/{req.inspected_quantity}, 尺寸: {req.dimension_verified}, 光学: {req.optical_verified})"
        order.updated_by_id = user_id
        await db.commit()
        await db.refresh(order)
        return order
