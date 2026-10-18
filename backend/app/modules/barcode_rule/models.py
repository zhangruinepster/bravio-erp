import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Text
from app.models.base import BaseAuditModel

class BarcodeLevel(str, enum.Enum):
    SN = "SN"           # 单品序列号 (32位激光码)
    BOX = "BOX"         # 彩盒码 (一盒双灯)
    CARTON = "CARTON"   # 外箱码 (SSCC-18 标准兼容)
    PALLET = "PALLET"   # 托盘码

class BarcodeRule(BaseAuditModel):
    """
    可配置条码规则定义 (docs/12)
    """
    __tablename__ = "barcode_rules"

    name = Column(String(100), nullable=False)
    level = Column(SQLEnum(BarcodeLevel), nullable=False, index=True)
    template = Column(String(255), nullable=False)       # 如: "{BRAVIO_ID}{REV}{YEAR_WEEK}{SEQ}{BIN}"
    regex_pattern = Column(String(255), nullable=False)  # 逆向解析正则
    is_default = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
