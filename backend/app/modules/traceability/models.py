import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey, Text
from app.models.base import BaseAuditModel

class PairingStatus(str, enum.Enum):
    MATCHED = "MATCHED"       # Binning 100% 匹配合格
    MISMATCH = "MISMATCH"     # 档位差异防呆拦截 (Poka-Yoke Blocked)
    SINGLE = "SINGLE"         # 待匹配第二支单件

class LaserSerialCode(BaseAuditModel):
    """
    32位激光微距码实体 (docs/07)
    结构: 5位Bravio料号 + 1位Revision + 4位年周 + 8位流水 + 14位Binning
    """
    __tablename__ = "laser_serial_codes"

    serial_number = Column(String(32), unique=True, nullable=False, index=True) # 32位唯一码
    product_id = Column(String(36), ForeignKey("product_masters.id"), nullable=False, index=True)
    bravio_id = Column(String(10), nullable=False)
    revision = Column(String(5), default="A", nullable=False)
    year_week = Column(String(4), nullable=False) # 如 "2642"
    sequence_no = Column(String(8), nullable=False)
    
    # LED 档位参数 (Binning)
    color_temp_bin = Column(String(20), default="6000K", nullable=False) # 色温档位
    flux_bin = Column(String(20), default="1200LM", nullable=False)       # 光通量档位
    voltage_bin = Column(String(20), default="12V", nullable=False)       # 正向电压档位
    raw_bin_code = Column(String(14), nullable=False)
    
    # 装配与配对状态
    is_paired = Column(Boolean, default=False, nullable=False)
    paired_box_id = Column(String(36), nullable=True, index=True)
    station_id = Column(String(50), default="STATION-PACK-01")
    notes = Column(Text, nullable=True)

class PairingRecord(BaseAuditModel):
    """
    一盒双支工位防呆配对流水表
    """
    __tablename__ = "pairing_records"

    box_barcode = Column(String(50), nullable=False, index=True)
    sn_first = Column(String(32), nullable=False)
    sn_second = Column(String(32), nullable=False)
    pairing_status = Column(SQLEnum(PairingStatus), default=PairingStatus.MATCHED, nullable=False)
    mismatch_reason = Column(String(200), nullable=True)
    station_operator = Column(String(80), nullable=False)
