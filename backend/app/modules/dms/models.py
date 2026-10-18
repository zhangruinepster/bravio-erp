import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Text
from app.models.base import BaseAuditModel

class IsoDocLevel(str, enum.Enum):
    LEVEL_1_MANUAL = "LEVEL_1_MANUAL"         # 一级质量手册 (QM)
    LEVEL_2_PROCEDURE = "LEVEL_2_PROCEDURE"   # 二级程序文件 (QP)
    LEVEL_3_WI = "LEVEL_3_WI"                 # 三级作业指导书 (WI)
    LEVEL_4_FORM = "LEVEL_4_FORM"             # 四级记录表单 (QF)

class DocStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED_EFFECTIVE = "APPROVED_EFFECTIVE" # 受控发布生效
    OBSOLETE = "OBSOLETE"                     # 作废归档

class ControlledDocument(BaseAuditModel):
    """
    ISO 9001 全局受控文档档案 (docs/15)
    """
    __tablename__ = "controlled_documents"

    doc_number = Column(String(50), unique=True, nullable=False, index=True) # 如 "WI-QA-001"
    title = Column(String(150), nullable=False)
    doc_level = Column(SQLEnum(IsoDocLevel), default=IsoDocLevel.LEVEL_3_WI, nullable=False, index=True)
    version = Column(String(10), default="V1.0", nullable=False)
    department_scope = Column(String(50), default="ALL")                     # 适用部门
    
    file_url = Column(Text, nullable=True)                                   # 文档存储路径
    watermark_text = Column(String(100), default="Bravio Confidential")      # 动态防泄密水印
    status = Column(SQLEnum(DocStatus), default=DocStatus.APPROVED_EFFECTIVE, nullable=False, index=True)
    summary = Column(Text, nullable=True)
