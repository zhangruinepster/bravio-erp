import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import InspectionSheet, EightDIncident, EightDStatus
from .schemas import InspectionCreate, EightDCreate, EightDUpdate

class QmsService:
    @staticmethod
    async def list_inspections(db: AsyncSession, product_id: Optional[str] = None) -> List[InspectionSheet]:
        stmt = select(InspectionSheet).where(InspectionSheet.is_deleted == False).order_by(InspectionSheet.created_at.desc())
        if product_id:
            stmt = stmt.where(InspectionSheet.product_id == product_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_inspection(db: AsyncSession, data: InspectionCreate, inspector_name: str, user_id: str) -> InspectionSheet:
        sheet_num = f"QC-{time.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        sheet = InspectionSheet(
            sheet_number=sheet_num,
            inspector_name=inspector_name,
            **data.model_dump(),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(sheet)
        await db.commit()
        await db.refresh(sheet)
        return sheet

    @staticmethod
    async def list_eight_d(db: AsyncSession) -> List[EightDIncident]:
        stmt = select(EightDIncident).where(EightDIncident.is_deleted == False).order_by(EightDIncident.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_eight_d(db: AsyncSession, data: EightDCreate, user_id: str) -> EightDIncident:
        inc_num = f"8D-{time.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        inc = EightDIncident(
            incident_number=inc_num,
            status=EightDStatus.OPEN,
            **data.model_dump(),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(inc)
        await db.commit()
        await db.refresh(inc)
        return inc

    @staticmethod
    async def update_eight_d(db: AsyncSession, incident_id: str, data: EightDUpdate, user_id: str) -> EightDIncident:
        stmt = select(EightDIncident).where(EightDIncident.id == incident_id, EightDIncident.is_deleted == False)
        inc = (await db.execute(stmt)).scalar_one_or_none()
        if not inc:
            raise HTTPException(status_code=404, detail="8D 攻关档案不存在")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(inc, k, v)
        inc.updated_by_id = user_id
        await db.commit()
        await db.refresh(inc)
        return inc
