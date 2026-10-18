import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel

class PackagingUnitLevel(str, enum.Enum):
    SN = "SN"
    BOX = "BOX"
    CARTON = "CARTON"
    PALLET = "PALLET"

class PackagingUnitStatus(str, enum.Enum):
    PACKED = "PACKED"                     # 已封箱封装
    IN_WAREHOUSE = "IN_WAREHOUSE"         # 在库
    SHIPPED = "SHIPPED"                   # 已出库发运
    PARTIAL_OPENED = "PARTIAL_OPENED"     # 抽检拆开 (余箱降级)
    LOOSE_SPARE_POOL = "LOOSE_SPARE_POOL" # 散件备用池 (售后/留样)

class PackagingUnit(BaseAuditModel):
    """
    四级包装单元聚合树实体 (SN -> BOX -> CARTON -> PALLET - docs/08)
    """
    __tablename__ = "packaging_units"

    unit_code = Column(String(50), unique=True, nullable=False, index=True) # 如 "CTN-99824-2642-0001"
    level = Column(SQLEnum(PackagingUnitLevel), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("packaging_units.id"), nullable=True, index=True)
    status = Column(SQLEnum(PackagingUnitStatus), default=PackagingUnitStatus.PACKED, nullable=False, index=True)
    
    product_id = Column(String(36), nullable=True)
    bravio_id = Column(String(10), nullable=True)
    warehouse_location = Column(String(50), default="MUC-WH-A-01") # 德国慕尼黑仓位
    notes = Column(Text, nullable=True)

    parent = relationship("PackagingUnit", remote_side="PackagingUnit.id", backref="children", lazy="selectin")
