from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from .schemas import BarcodeRuleCreate, BarcodeRuleResponse, BarcodeGenerateRequest, BarcodeParseRequest, BarcodeParseResponse
from .service import BarcodeRuleService

router = APIRouter(prefix="/barcode-rules", tags=["条码规则与解析引擎 (Barcode Engine)"])

@router.get("", response_model=List[BarcodeRuleResponse], summary="查询已定义的条码规则列表")
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await BarcodeRuleService.get_all(db)

@router.post("", response_model=BarcodeRuleResponse, status_code=status.HTTP_201_CREATED, summary="定义新条码规则模板")
async def create_rule(
    data: BarcodeRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await BarcodeRuleService.create(db, data, current_user.id)

@router.post("/generate", summary="正向生成合规条码文本")
async def generate_barcode(
    req: BarcodeGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    code = BarcodeRuleService.generate_barcode(req)
    return {"barcode": code, "level": req.level, "length": len(code)}

@router.post("/parse", response_model=BarcodeParseResponse, summary="逆向解析条码结构与字段")
async def parse_barcode(
    req: BarcodeParseRequest,
    current_user: User = Depends(get_current_user)
):
    return BarcodeRuleService.parse_barcode(req.barcode)
