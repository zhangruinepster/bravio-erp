import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Text
from app.models.base import BaseAuditModel

class RmaStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"                   # 客户提交申请
    UNDER_INSPECTION = "UNDER_INSPECTION"     # 德国售后中心实物验货中
    APPROVED = "APPROVED"                     # 验真合规，质保批准
    FRAUD_REJECTED = "FRAUD_REJECTED"         # 换盒欺诈/假件拦截
    COMPLETED = "COMPLETED"                   # 补发备件完成闭环

class RmaOrder(BaseAuditModel):
    """
    售后逆向风控与 RMA 工单 (docs/09)
    """
    __tablename__ = "rma_orders"

    rma_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "RMA-2026-0081"
    customer_name = Column(String(120), nullable=False)
    returned_sn = Column(String(32), nullable=False, index=True)      # 客户退回的单品序列号
    returned_box_code = Column(String(50), nullable=True)             # 客户退回的外包装彩盒码
    claim_reason = Column(Text, nullable=False)                       # 客户报障描述
    
    # 风控审计与防伪核验
    is_fraud_detected = Column(Boolean, default=False, nullable=False)# 换盒欺诈拦截标志
    fraud_reason = Column(String(255), nullable=True)                 # 欺诈拦截原因
    sample_location_matched = Column(String(80), nullable=True)       # 同批次慕尼黑留样库位
    replacement_sn = Column(String(32), nullable=True)                # 精准补发的同Bin散件SN
    
    status = Column(SQLEnum(RmaStatus), default=RmaStatus.SUBMITTED, nullable=False, index=True)
    inspector_notes = Column(Text, nullable=True)
