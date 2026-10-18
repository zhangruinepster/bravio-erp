from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import BillOfMaterial, BomItem, PackagingHierarchy
from .schemas import BomCreate

class BomService:
    @staticmethod
    async def get_by_product_id(db: AsyncSession, product_id: str) -> List[BillOfMaterial]:
        stmt = select(BillOfMaterial).where(
            BillOfMaterial.product_id == product_id,
            BillOfMaterial.is_deleted == False
        ).order_by(BillOfMaterial.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, bom_id: str) -> Optional[BillOfMaterial]:
        stmt = select(BillOfMaterial).where(BillOfMaterial.id == bom_id, BillOfMaterial.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: BomCreate, user_id: str) -> BillOfMaterial:
        # 新建 BOM
        bom = BillOfMaterial(
            product_id=data.product_id,
            version=data.version,
            description=data.description,
            is_active=True,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(bom)
        await db.flush()

        # 添加 BOM 明细项
        for item_data in data.items:
            item = BomItem(
                bom_id=bom.id,
                **item_data.model_dump(),
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(item)

        # 添加包装层级
        if data.packaging:
            pkg = PackagingHierarchy(
                bom_id=bom.id,
                **data.packaging.model_dump(),
                created_by_id=user_id,
                updated_by_id=user_id
            )
            db.add(pkg)

        await db.commit()
        await db.refresh(bom)
        return bom
