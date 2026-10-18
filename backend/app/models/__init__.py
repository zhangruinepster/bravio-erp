from app.models.base import BaseAuditModel
from app.models.user import User
from app.models.audit import AuditLog
from app.models.rbac import Role, Permission, DataScope, user_roles, role_permissions
from app.models.organization import (
    Department,
    JobPosition,
    Employee,
    EmployeeCertification,
    EmployeeTraining,
    IsoProcessType,
    EmployeeStatus,
)

# 导入 V0.3 新业务模块实体 (docs/05 ~ docs/17)
from app.modules.product.models import ProductMaster, ProductLifecycleStatus
from app.modules.bom.models import BillOfMaterial, BomItem, PackagingHierarchy, BomComponentCategory
from app.modules.barcode_rule.models import BarcodeRule, BarcodeLevel
from app.modules.ecm.models import EngineeringChangeOrder, EcoStatus, EcoChangeType
from app.modules.traceability.models import LaserSerialCode, PairingRecord, PairingStatus
from app.modules.wms.models import PackagingUnit, PackagingUnitLevel, PackagingUnitStatus
from app.modules.rma.models import RmaOrder, RmaStatus
from app.modules.qms.models import InspectionSheet, EightDIncident, InspectionType, InspectionResult, EightDStatus
from app.modules.dms.models import ControlledDocument, IsoDocLevel, DocStatus
from app.modules.partner.models import BusinessPartner, PartnerType
from app.modules.b2b.models import B2bWorkOrder, B2bWorkOrderStatus
from app.models.attachment import SystemAttachment

__all__ = [
    "SystemAttachment",
    "BaseAuditModel",
    "User",
    "AuditLog",
    "Role",
    "Permission",
    "DataScope",
    "user_roles",
    "role_permissions",
    "Department",
    "JobPosition",
    "Employee",
    "EmployeeCertification",
    "EmployeeTraining",
    "IsoProcessType",
    "EmployeeStatus",
    "ProductMaster",
    "ProductLifecycleStatus",
    "BillOfMaterial",
    "BomItem",
    "PackagingHierarchy",
    "BomComponentCategory",
    "BarcodeRule",
    "BarcodeLevel",
    "EngineeringChangeOrder",
    "EcoStatus",
    "EcoChangeType",
    "LaserSerialCode",
    "PairingRecord",
    "PairingStatus",
    "PackagingUnit",
    "PackagingUnitLevel",
    "PackagingUnitStatus",
    "RmaOrder",
    "RmaStatus",
    "InspectionSheet",
    "EightDIncident",
    "InspectionType",
    "InspectionResult",
    "EightDStatus",
    "ControlledDocument",
    "IsoDocLevel",
    "DocStatus",
    "BusinessPartner",
    "PartnerType",
    "B2bWorkOrder",
    "B2bWorkOrderStatus",
    "BackupRecord",
    "BackupType",
]
