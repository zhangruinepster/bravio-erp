import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.modules.traceability.models import LaserSerialCode
from .models import RmaOrder, RmaStatus
from .schemas import RmaCreateRequest, RmaInspectRequest

class RmaService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[RmaOrder]:
        stmt = select(RmaOrder).where(RmaOrder.is_deleted == False).order_by(RmaOrder.created_at.desc())
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, rma_id: str) -> Optional[RmaOrder]:
        stmt = select(RmaOrder).where(RmaOrder.id == rma_id, RmaOrder.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def submit_rma(db: AsyncSession, req: RmaCreateRequest, user_id: str) -> RmaOrder:
        """
        售后退货申请与自动换盒欺诈核验 (docs/09)
        """
        rma_num = f"RMA-{time.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        
        # 1. 查找原始出厂登记记录
        sn_stmt = select(LaserSerialCode).where(LaserSerialCode.serial_number == req.returned_sn, LaserSerialCode.is_deleted == False)
        sn_record = (await db.execute(sn_stmt)).scalar_one_or_none()

        is_fraud = False
        fraud_msg = None
        sample_loc = "MUC-LAB-SHELF-04B" # 默认同批次慕尼黑留样货架

        if not sn_record:
            is_fraud = True
            fraud_msg = "非 Bravio 正品零件号，数据库无该激光微距序列号物理刻印档案！"
        else:
            # 核对彩盒关联 (换盒欺诈比对)
            if req.returned_box_code and sn_record.paired_box_id:
                if req.returned_box_code != sn_record.paired_box_id:
                    is_fraud = True
                    fraud_msg = f"换盒欺诈拦截：退回彩盒码({req.returned_box_code}) 与该序列号出厂绑定彩盒({sn_record.paired_box_id}) 不符！"

        order = RmaOrder(
            rma_number=rma_num,
            customer_name=req.customer_name,
            returned_sn=req.returned_sn,
            returned_box_code=req.returned_box_code,
            claim_reason=req.claim_reason,
            is_fraud_detected=is_fraud,
            fraud_reason=fraud_msg,
            sample_location_matched=sample_loc,
            status=RmaStatus.FRAUD_REJECTED if is_fraud else RmaStatus.UNDER_INSPECTION,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def approve_and_dispatch_replacement(db: AsyncSession, rma_id: str, req: RmaInspectRequest, user_id: str) -> RmaOrder:
        order = await RmaService.get_by_id(db, rma_id)
        if not order:
            raise HTTPException(status_code=404, detail="RMA 工单不存在")
        if order.is_fraud_detected:
            raise HTTPException(status_code=400, detail="该工单已被标记欺诈拦截，禁止批准补发！")

        order.status = RmaStatus.COMPLETED
        order.replacement_sn = req.replacement_sn
        order.inspector_notes = req.inspector_notes
        order.updated_by_id = user_id
        await db.commit()
        await db.refresh(order)
        return order
