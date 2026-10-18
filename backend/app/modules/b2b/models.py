import enum
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, Text
from app.models.base import BaseAuditModel

class B2bWorkOrderStatus(str, enum.Enum):
    RELEASED = "RELEASED"             # 工单已下达给代工厂
    IN_PRODUCTION = "IN_PRODUCTION"   # 外协加工中
    FQC_SUBMITTED = "FQC_SUBMITTED"   # 代工厂已上传检验结果
    SHIPPED = "SHIPPED"               # 已发往德国仓
    COMPLETED = "COMPLETED"           # 德国仓完成接收

class B2bWorkOrder(BaseAuditModel):
    """
    外部代工协同工单 (docs/16)
    """
    __tablename__ = "b2b_work_orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "WO-OEM-2026-001"
    partner_id = Column(String(36), ForeignKey("business_partners.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("product_masters.id"), nullable=False, index=True)
    bravio_id = Column(String(10), nullable=False)
    planned_quantity = Column(Integer, default=500, nullable=False)
    
    # 预分配条码段
    sn_range_start = Column(String(32), nullable=True)
    sn_range_end = Column(String(32), nullable=True)
    
    status = Column(SQLEnum(B2bWorkOrderStatus), default=B2bWorkOrderStatus.RELEASED, nullable=False, index=True)
    notes = Column(Text, nullable=True)
