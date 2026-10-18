from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .models import IsoDocLevel
from .schemas import DocumentCreate, DocumentResponse
from .service import DmsService

router = APIRouter(prefix="/dms", tags=["受控文档管理与质量体系知识库 (DMS)"])

@router.get("/documents", response_model=List[DocumentResponse], summary="查询受控文档清单 (按ISO金字塔分级)")
async def list_documents(
    level: Optional[IsoDocLevel] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await DmsService.list_documents(db, level)

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="上报与归档新受控体系文档")
async def create_document(
    data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await DmsService.create(db, data, current_user.id)
