import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import BarcodeRule, BarcodeLevel
from .schemas import BarcodeRuleCreate, BarcodeGenerateRequest, BarcodeParseResponse

class BarcodeRuleService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[BarcodeRule]:
        stmt = select(BarcodeRule).where(BarcodeRule.is_deleted == False).order_by(BarcodeRule.level)
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def create(db: AsyncSession, data: BarcodeRuleCreate, user_id: str) -> BarcodeRule:
        rule = BarcodeRule(**data.model_dump(), created_by_id=user_id, updated_by_id=user_id)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    def generate_barcode(req: BarcodeGenerateRequest) -> str:
        """根据当前层级与参数生成标准条码"""
        now = datetime.now(timezone.utc)
        yw = req.year_week or f"{now.strftime('%y')}{now.isocalendar()[1]:02d}"
        seq_str = f"{req.sequence:08d}"

        if req.level == BarcodeLevel.SN:
            # 32位激光微距刻印码: 5位零件号 + 1位版本 + 4位年周 + 8位序列流水 + 14位Binning
            bin_clean = (req.binning or "DEFAULTBIN").replace("-", "").ljust(14, "0")[:14]
            return f"{req.bravio_id[:5]:0>5}{req.revision[:1]}{yw}{seq_str}{bin_clean}"
        elif req.level == BarcodeLevel.BOX:
            return f"BOX-{req.bravio_id}-{yw}-{seq_str[:6]}"
        elif req.level == BarcodeLevel.CARTON:
            return f"CTN-{req.bravio_id}-{yw}-{seq_str[:5]}"
        else: # PALLET
            return f"PLT-{req.bravio_id}-{yw}-{seq_str[:4]}"

    @staticmethod
    def parse_barcode(barcode: str) -> BarcodeParseResponse:
        """逆向解析条码"""
        b = barcode.strip()
        if len(b) == 32 and not b.startswith(("BOX-", "CTN-", "PLT-")):
            # 32位激光序列号
            return BarcodeParseResponse(
                raw_barcode=b,
                level="SN",
                is_valid=True,
                parsed_fields={
                    "bravio_id": b[0:5],
                    "revision": b[5:6],
                    "year_week": b[6:10],
                    "sequence": b[10:18],
                    "binning_raw": b[18:32]
                }
            )
        elif b.startswith("BOX-"):
            parts = b.split("-")
            return BarcodeParseResponse(
                raw_barcode=b,
                level="BOX",
                is_valid=len(parts) >= 4,
                parsed_fields={"bravio_id": parts[1] if len(parts) > 1 else "", "year_week": parts[2] if len(parts) > 2 else ""}
            )
        elif b.startswith("CTN-"):
            parts = b.split("-")
            return BarcodeParseResponse(
                raw_barcode=b,
                level="CARTON",
                is_valid=len(parts) >= 4,
                parsed_fields={"bravio_id": parts[1] if len(parts) > 1 else "", "year_week": parts[2] if len(parts) > 2 else ""}
            )
        elif b.startswith("PLT-"):
            parts = b.split("-")
            return BarcodeParseResponse(
                raw_barcode=b,
                level="PALLET",
                is_valid=len(parts) >= 4,
                parsed_fields={"bravio_id": parts[1] if len(parts) > 1 else "", "year_week": parts[2] if len(parts) > 2 else ""}
            )
        return BarcodeParseResponse(raw_barcode=b, level="UNKNOWN", is_valid=False, parsed_fields={})
