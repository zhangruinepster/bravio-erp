from sqlalchemy import Column, String, Integer, Text
from app.models.base import BaseAuditModel

class SystemAttachment(BaseAuditModel):
    """
    系统全局受控附件与多媒体资产元数据表 (遵循 ISO 9001 / KBA CoP 防篡改合规要求 - docs/05 & docs/15)
    数据库只存储轻量级文件指纹与关联元数据，实体二进制文件独立持久化于物理存储卷
    """
    __tablename__ = "sys_attachments"

    file_name = Column(String(255), nullable=False, index=True)         # 原始文件名 (如 avatar_dr_zhang.png)
    stored_name = Column(String(255), nullable=False, unique=True)       # 存储唯一文件名 (防重名与路径穿透)
    content_type = Column(String(100), nullable=False)                  # MIME 类型 (如 image/png, image/jpeg)
    file_size = Column(Integer, nullable=False, default=0)              # 文件大小 (Bytes)
    file_path = Column(Text, nullable=False)                            # 物理存储绝对或相对路径
    file_url = Column(Text, nullable=False)                             # 前端直接访问的网络相对路径 (如 /uploads/...)
    sha256_hash = Column(String(64), nullable=False, index=True)        # SHA-256 完整性防篡改哈希
    
    # 业务关联模型 (支持 HR 员工、产品主数据、受控文档等通用关联)
    res_model = Column(String(50), nullable=False, index=True)          # 如 "hr_employee", "product_master", "dms_document"
    res_id = Column(String(36), nullable=True, index=True)              # 目标业务实体 ID
    description = Column(String(255), nullable=True)                    # 说明备注 (如 "员工档案头像", "产品CAD渲染图")

    def __repr__(self):
        return f"<SystemAttachment name={self.file_name} model={self.res_model} size={self.file_size}>"
