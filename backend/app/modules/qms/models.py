import enum
from sqlalchemy import Column, String, Boolean, Integer, Float, Enum as SQLEnum, Text, ForeignKey
from app.models.base import BaseAuditModel

class InspectionType(str, enum.Enum):
    IQC = "IQC"   # 进料检验 (德国仓/原材料)
    IPQC = "IPQC" # 生产过程巡检
    FQC = "FQC"   # 制造端成品最终出厂质检

class InspectionResult(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL_RELEASE = "CONDITIONAL_RELEASE" # 特批让步放行

class InspectionSheet(BaseAuditModel):
    """
    全流程质检单 (docs/14)
    """
    __tablename__ = "inspection_sheets"

    sheet_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "QC-2026-0092"
    inspection_type = Column(SQLEnum(InspectionType), default=InspectionType.FQC, nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("product_masters.id"), nullable=False, index=True)
    bravio_id = Column(String(10), nullable=False)
    batch_number = Column(String(50), nullable=False)                         # 生产批次
    
    sample_size = Column(Integer, default=5, nullable=False)                  # 抽样数
    defect_count = Column(Integer, default=0, nullable=False)                 # 不良数
    dimension_check_passed = Column(Boolean, default=True, nullable=False)    # 关键特殊特性尺寸合格
    optical_check_passed = Column(Boolean, default=True, nullable=False)      # 光学特性合格
    kba_cop_compliant = Column(Boolean, default=True, nullable=False)         # 德国 KBA 生产一致性达标
    
    overall_result = Column(SQLEnum(InspectionResult), default=InspectionResult.PASS, nullable=False)
    inspector_name = Column(String(80), nullable=False)
    notes = Column(Text, nullable=True)

class EightDStatus(str, enum.Enum):
    OPEN = "OPEN"               # 启动异常攻关 (D0-D2)
    ROOT_CAUSE = "ROOT_CAUSE"   # 根本原因锁定 (D3-D4)
    CAPA_ACTIONS = "CAPA_ACTIONS"# 纠正措施验证 (D5-D6)
    CLOSED = "CLOSED"           # 标准化与表彰闭环 (D7-D8)

class EightDIncident(BaseAuditModel):
    """
    质量 8D 失效管理与 CAPA 闭环 (docs/14)
    """
    __tablename__ = "eight_d_incidents"

    incident_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "8D-2026-001"
    title = Column(String(150), nullable=False)
    product_id = Column(String(36), nullable=False)
    source = Column(String(50), default="CUSTOMER_COMPLAINT") # 客户投诉 / 出厂拦截 / 德国仓IQC
    status = Column(SQLEnum(EightDStatus), default=EightDStatus.OPEN, nullable=False, index=True)
    
    d1_team_leader = Column(String(80), nullable=True)
    d2_problem_description = Column(Text, nullable=False)
    d3_interim_containment = Column(Text, nullable=True)     # 围堵遏制措施
    d4_root_cause = Column(Text, nullable=True)              # 5-Why 根本原因分析
    d5_permanent_corrective = Column(Text, nullable=True)    # 永久纠正措施
    d7_prevent_recurrence = Column(Text, nullable=True)      # 预防再发生/修改SOP与FMEA
    closure_notes = Column(Text, nullable=True)
