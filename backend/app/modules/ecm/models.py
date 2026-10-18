import enum
from sqlalchemy import Column, String, Boolean, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel

class EcoStatus(str, enum.Enum):
    DRAFT = "DRAFT"                   # 草拟
    UNDER_REVIEW = "UNDER_REVIEW"     # 评审中 (技术/质量/KBA)
    APPROVED = "APPROVED"             # 已核准批准
    REJECTED = "REJECTED"             # 已驳回
    RELEASED = "RELEASED"             # 已发布永久锁定 (ECN 闭环)

class EcoChangeType(str, enum.Enum):
    DESIGN = "DESIGN"                 # 结构或电路图纸变更
    BOM = "BOM"                       # 物料替代料变更
    PROCESS = "PROCESS"               # 生产工艺与工装变更
    KBA_REGULATORY = "KBA_REGULATORY" # 涉及 ECE/KBA 法规与型式认证参数更新

class EngineeringChangeOrder(BaseAuditModel):
    """
    工程变更指令 (ECO - docs/13)
    """
    __tablename__ = "engineering_change_orders"

    eco_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "ECO-2026-001"
    product_id = Column(String(36), ForeignKey("product_masters.id"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    change_type = Column(SQLEnum(EcoChangeType), default=EcoChangeType.DESIGN, nullable=False)
    reason = Column(Text, nullable=False)
    
    # 四大证据包与影响分析
    affects_drawings = Column(Boolean, default=True)
    affects_bom = Column(Boolean, default=False)
    affects_kba_homologation = Column(Boolean, default=False) # 涉及KBA型式认证强制标记
    kba_eval_notes = Column(Text, nullable=True)             # KBA 认证变更合规评价说明
    
    status = Column(SQLEnum(EcoStatus), default=EcoStatus.DRAFT, nullable=False, index=True)
    approver_name = Column(String(80), nullable=True)
    approval_notes = Column(Text, nullable=True)
