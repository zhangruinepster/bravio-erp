import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Text, Integer
from app.models.base import BaseAuditModel

class PartnerType(str, enum.Enum):
    SUPPLIER = "SUPPLIER"     # 供应商 / 外协代工厂
    CUSTOMER = "CUSTOMER"     # B2B 客户 / 主机厂 / 采购商
    BOTH = "BOTH"             # 双重身份

class BusinessPartner(BaseAuditModel):
    """
    商业伙伴通用档案 (docs/17)
    """
    __tablename__ = "business_partners"

    partner_code = Column(String(50), unique=True, nullable=False, index=True) # 如 "SUP-DE-001" 或 "CUST-OEM-01"
    name = Column(String(150), nullable=False)
    partner_type = Column(SQLEnum(PartnerType), default=PartnerType.SUPPLIER, nullable=False, index=True)
    contact_person = Column(String(80), nullable=True)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # 供应商专属属性
    is_oem_certified = Column(Boolean, default=False)               # 是否具备车规代工资质
    api_token = Column(String(64), nullable=True, unique=True)      # 外部集成 API Token
    
    # 商务条款
    payment_terms_days = Column(Integer, default=60)                # 账期天数 (如 Net 60)
    shipping_address = Column(Text, nullable=True)                  # 收发货地址
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
