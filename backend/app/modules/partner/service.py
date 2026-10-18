import secrets
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import BusinessPartner, PartnerType
from .schemas import PartnerCreate, PartnerUpdate

class PartnerService:
    @staticmethod
    async def list_partners(db: AsyncSession, partner_type: Optional[PartnerType] = None) -> List[BusinessPartner]:
        stmt = select(BusinessPartner).where(BusinessPartner.is_deleted == False)
        if partner_type:
            stmt = stmt.where(BusinessPartner.partner_type == partner_type)
        stmt = stmt.order_by(BusinessPartner.partner_code)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, partner_id: str) -> Optional[BusinessPartner]:
        stmt = select(BusinessPartner).where(BusinessPartner.id == partner_id, BusinessPartner.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: PartnerCreate, user_id: str) -> BusinessPartner:
        stmt = select(BusinessPartner).where(BusinessPartner.partner_code == data.partner_code, BusinessPartner.is_deleted == False)
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"商业伙伴编号 [{data.partner_code}] 已存在")

        token = f"m2m_{secrets.token_hex(24)}"
        partner = BusinessPartner(
            **data.model_dump(),
            api_token=token,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(partner)
        await db.commit()
        await db.refresh(partner)
        return partner

    @staticmethod
    async def update(db: AsyncSession, partner_id: str, data: "PartnerUpdate", user_id: str) -> BusinessPartner:
        partner = await PartnerService.get_by_id(db, partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="商业伙伴档案不存在")

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(partner, key, value)

        partner.updated_by_id = user_id
        await db.commit()
        await db.refresh(partner)
        return partner

