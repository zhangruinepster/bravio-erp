from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from .models import ProductMaster, ProductLifecycleStatus
from .schemas import ProductCreate, ProductUpdate

class ProductService:
    @staticmethod
    async def get_all(db: AsyncSession, category: Optional[str] = None) -> List[ProductMaster]:
        stmt = select(ProductMaster).where(ProductMaster.is_deleted == False).order_by(ProductMaster.bravio_id)
        if category:
            stmt = stmt.where(ProductMaster.category == category)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, product_id: str) -> Optional[ProductMaster]:
        stmt = select(ProductMaster).where(ProductMaster.id == product_id, ProductMaster.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_by_bravio_id(db: AsyncSession, bravio_id: str) -> Optional[ProductMaster]:
        stmt = select(ProductMaster).where(ProductMaster.bravio_id == bravio_id, ProductMaster.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: ProductCreate, user_id: str) -> ProductMaster:
        exist = await ProductService.get_by_bravio_id(db, data.bravio_id)
        if exist:
            raise HTTPException(status_code=400, detail=f"Bravio 零件号 [{data.bravio_id}] 已存在")

        product = ProductMaster(
            **data.model_dump(),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def update(db: AsyncSession, product_id: str, data: ProductUpdate, user_id: str) -> ProductMaster:
        product = await ProductService.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品档案不存在")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(product, k, v)
        product.updated_by_id = user_id
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def advance_lifecycle(db: AsyncSession, product_id: str, target_status: ProductLifecycleStatus, user_id: str) -> ProductMaster:
        product = await ProductService.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品档案不存在")
        
        product.lifecycle_status = target_status
        # 同步推升阶段门编号
        status_gate_map = {
            ProductLifecycleStatus.PROJECT_KICKOFF: 1,
            ProductLifecycleStatus.A_SAMPLE: 2,
            ProductLifecycleStatus.B_SAMPLE: 3,
            ProductLifecycleStatus.PPAP_SIGN_OFF: 4,
            ProductLifecycleStatus.MASS_PRODUCTION_SOP: 5,
            ProductLifecycleStatus.END_OF_PRODUCTION_EOP: 5
        }
        product.current_phase_gate = status_gate_map.get(target_status, product.current_phase_gate)
        product.updated_by_id = user_id
        await db.commit()
        await db.refresh(product)
        return product
