import enum
from sqlalchemy import Column, String, Boolean, Integer, Text, Enum as SQLEnum
from app.models.base import BaseAuditModel

class ProductLifecycleStatus(str, enum.Enum):
    PROJECT_KICKOFF = "PROJECT_KICKOFF"          # 项目立项阶段
    A_SAMPLE = "A_SAMPLE"                        # A样验证 (功能概念件)
    B_SAMPLE = "B_SAMPLE"                        # B样验证 (设计验证 DVP)
    PPAP_SIGN_OFF = "PPAP_SIGN_OFF"              # PPAP 签署 (试产件批准)
    MASS_PRODUCTION_SOP = "MASS_PRODUCTION_SOP"  # 量产中 (SOP / 生产一致性监控)
    END_OF_PRODUCTION_EOP = "END_OF_PRODUCTION_EOP"# 停产归档 (EOP / 仅供售后备件)

class ProductMaster(BaseAuditModel):
    """
    汽车级产品主数据模型 (遵循 ISO 9001 & KBA Type Approval 合规规范 - docs/10)
    """
    __tablename__ = "product_masters"

    bravio_id = Column(String(10), unique=True, nullable=False, index=True) # 5位唯一物料号
    product_name = Column(String(150), nullable=False)
    current_revision = Column(String(5), default="A", nullable=False)
    category = Column(String(50), nullable=False, default="HEADLIGHT") # HEADLIGHT, DRL, TAILLIGHT, DRIVER_BOARD
    
    primary_image_url = Column(Text, nullable=True)
    technical_spec_pdf_url = Column(Text, nullable=True)
    
    # KBA 认证与法规属性
    is_certified = Column(Boolean, default=True, nullable=False)
    kba_approval_number = Column(String(60), nullable=True) # E1-149R-001234
    homologation_authority = Column(String(60), default="KBA-Flensburg")
    iso_classification = Column(String(50), default="SAFETY_RELEVANT")
    
    # 追溯与序列化
    is_serialized = Column(Boolean, default=True, nullable=False)
    standard_warranty_months = Column(Integer, default=24)
    
    # APQP 阶段门生命周期
    lifecycle_status = Column(SQLEnum(ProductLifecycleStatus), default=ProductLifecycleStatus.PROJECT_KICKOFF, nullable=False)
    current_phase_gate = Column(Integer, default=1) # 1 到 5 阶段门
    notes = Column(Text, nullable=True)
