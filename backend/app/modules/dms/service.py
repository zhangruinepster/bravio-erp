from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import ControlledDocument, IsoDocLevel
from .schemas import DocumentCreate

class DmsService:
    @staticmethod
    async def list_documents(db: AsyncSession, level: Optional[IsoDocLevel] = None) -> List[ControlledDocument]:
        stmt = select(ControlledDocument).where(ControlledDocument.is_deleted == False)
        if level:
            stmt = stmt.where(ControlledDocument.doc_level == level)
        stmt = stmt.order_by(ControlledDocument.doc_level, ControlledDocument.doc_number)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, data: DocumentCreate, user_id: str) -> ControlledDocument:
        stmt = select(ControlledDocument).where(ControlledDocument.doc_number == data.doc_number, ControlledDocument.is_deleted == False)
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"受控文档编号 [{data.doc_number}] 已存在")

        doc = ControlledDocument(
            **data.model_dump(),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc
