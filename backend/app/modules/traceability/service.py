from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import LaserSerialCode, PairingRecord, PairingStatus
from .schemas import LaserCodeCreate, PairingCheckRequest, PairingCheckResponse

class TraceabilityService:
    @staticmethod
    async def create_laser_code(db: AsyncSession, data: LaserCodeCreate, user_id: str) -> LaserSerialCode:
        now = datetime.now(timezone.utc)
        yw = f"{now.strftime('%y')}{now.isocalendar()[1]:02d}"
        seq_str = f"{data.sequence_int:08d}"
        bin_clean = f"{data.color_temp_bin}{data.flux_bin}{data.voltage_bin}".replace("-", "").replace(" ", "").ljust(14, "0")[:14]
        
        # 组装 32 位激光码
        sn_32 = f"{data.bravio_id[:5]:0>5}{data.revision[:1]}{yw}{seq_str}{bin_clean}"

        code = LaserSerialCode(
            serial_number=sn_32,
            product_id=data.product_id,
            bravio_id=data.bravio_id,
            revision=data.revision,
            year_week=yw,
            sequence_no=seq_str,
            color_temp_bin=data.color_temp_bin,
            flux_bin=data.flux_bin,
            voltage_bin=data.voltage_bin,
            raw_bin_code=bin_clean,
            station_id=data.station_id,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(code)
        await db.commit()
        await db.refresh(code)
        return code

    @staticmethod
    async def get_by_sn(db: AsyncSession, sn: str) -> Optional[LaserSerialCode]:
        stmt = select(LaserSerialCode).where(LaserSerialCode.serial_number == sn, LaserSerialCode.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def check_and_pair_box(db: AsyncSession, req: PairingCheckRequest, operator_name: str, user_id: str) -> PairingCheckResponse:
        """
        一盒双支工位防呆核心逻辑 (色温/光通量/电压 Binning 100% 强比对 - docs/07)
        """
        code_1 = await TraceabilityService.get_by_sn(db, req.sn_first)
        code_2 = await TraceabilityService.get_by_sn(db, req.sn_second)

        if not code_1 or not code_2:
            return PairingCheckResponse(
                is_pass=False,
                status=PairingStatus.MISMATCH,
                box_barcode=req.box_barcode,
                message="防呆阻断：输入的激光序列号在生产主数据库中未登记！",
                sn_first=req.sn_first,
                sn_second=req.sn_second,
                first_bin="未知",
                second_bin="未知"
            )

        bin_1 = f"{code_1.color_temp_bin}-{code_1.flux_bin}-{code_1.voltage_bin}"
        bin_2 = f"{code_2.color_temp_bin}-{code_2.flux_bin}-{code_2.voltage_bin}"

        # 强比对防呆判定
        is_matched = (
            code_1.color_temp_bin == code_2.color_temp_bin and
            code_1.flux_bin == code_2.flux_bin and
            code_1.voltage_bin == code_2.voltage_bin
        )

        status_result = PairingStatus.MATCHED if is_matched else PairingStatus.MISMATCH
        reason = None if is_matched else f"Binning 档位不匹配：第一支({bin_1}) vs 第二支({bin_2})"

        # 记录配对日志
        rec = PairingRecord(
            box_barcode=req.box_barcode,
            sn_first=req.sn_first,
            sn_second=req.sn_second,
            pairing_status=status_result,
            mismatch_reason=reason,
            station_operator=operator_name,
            created_by_id=user_id,
            updated_by_id=user_id
        )
        db.add(rec)

        if is_matched:
            code_1.is_paired = True
            code_1.paired_box_id = req.box_barcode
            code_2.is_paired = True
            code_2.paired_box_id = req.box_barcode

        await db.commit()

        return PairingCheckResponse(
            is_pass=is_matched,
            status=status_result,
            box_barcode=req.box_barcode,
            message="✓ 配对成功：双灯 Binning 档位 100% 吻合，允许封盒装箱！" if is_matched else f"✕ 防呆声光报警拦截：{reason}",
            sn_first=req.sn_first,
            sn_second=req.sn_second,
            first_bin=bin_1,
            second_bin=bin_2
        )
