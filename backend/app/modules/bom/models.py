import enum
from sqlalchemy import Column, String, Boolean, Integer, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel

class BomComponentCategory(str, enum.Enum):
    ASSEMBLY = "ASSEMBLY"         # 子总成/PCBA
    PART = "PART"                 # 电子/结构零件
    MANUAL = "MANUAL"             # 说明书与合格证成文纸张
    PACKAGING = "PACKAGING"       # 吸塑/珍珠棉/彩盒包材

class BillOfMaterial(BaseAuditModel):
    """
    轻量级汽车级物料清单 (BOM - docs/11)
    """
    __tablename__ = "boms"

    product_id = Column(String(36), ForeignKey("product_masters.id"), nullable=False, index=True)
    version = Column(String(10), default="V1.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)

    items = relationship("BomItem", back_populates="bom", cascade="all, delete-orphan", lazy="selectin")
    packaging = relationship("PackagingHierarchy", back_populates="bom", uselist=False, cascade="all, delete-orphan", lazy="selectin")

class BomItem(BaseAuditModel):
    __tablename__ = "bom_items"

    bom_id = Column(String(36), ForeignKey("boms.id"), nullable=False, index=True)
    part_number = Column(String(60), nullable=False)
    part_name = Column(String(120), nullable=False)
    category = Column(SQLEnum(BomComponentCategory), default=BomComponentCategory.PART, nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit = Column(String(20), default="PCS", nullable=False)
    reference_designator = Column(String(100), nullable=True) # 如 "U1, C12, LED1"
    is_safety_critical = Column(Boolean, default=False)       # 是否为关键安全特性零件

    bom = relationship("BillOfMaterial", back_populates="items")

class PackagingHierarchy(BaseAuditModel):
    """
    出货包装层级规范 (彩盒 -> 外箱 -> 托盘)
    """
    __tablename__ = "packaging_hierarchies"

    bom_id = Column(String(36), ForeignKey("boms.id"), nullable=False, unique=True)
    pieces_per_box = Column(Integer, default=2, nullable=False)       # 每彩盒支数 (一盒双灯默认 2)
    boxes_per_carton = Column(Integer, default=20, nullable=False)    # 每外箱盒数
    cartons_per_pallet = Column(Integer, default=24, nullable=False)  # 每托盘外箱数
    box_spec = Column(String(100), default="220x150x80mm")
    carton_spec = Column(String(100), default="620x450x340mm")
    notes = Column(Text, nullable=True)

    bom = relationship("BillOfMaterial", back_populates="packaging")
