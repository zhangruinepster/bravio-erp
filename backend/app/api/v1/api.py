from fastapi import APIRouter
from app.api.v1.endpoints import auth, system, organization, rbac
from app.modules.product import product_router
from app.modules.bom import bom_router
from app.modules.barcode_rule import barcode_rule_router
from app.modules.ecm import ecm_router
from app.modules.traceability import traceability_router
from app.modules.wms import wms_router
from app.modules.rma import rma_router
from app.modules.qms import qms_router
from app.modules.dms import dms_router
from app.modules.partner import partner_router
from app.modules.b2b import b2b_router
from app.modules.system_backup import system_backup_router

api_router = APIRouter()

# 基础鉴权与运维
api_router.include_router(auth.router)
api_router.include_router(system.router)
api_router.include_router(rbac.router, prefix="/rbac", tags=["权限与角色控制中心"])
api_router.include_router(organization.router, prefix="/org", tags=["组织架构与人员资质合规"])

# V0.3 新业务模块 (docs/05 ~ docs/17)
api_router.include_router(product_router)
api_router.include_router(bom_router)
api_router.include_router(barcode_rule_router)
api_router.include_router(ecm_router)
api_router.include_router(traceability_router)
api_router.include_router(wms_router)
api_router.include_router(rma_router)
api_router.include_router(qms_router)
api_router.include_router(dms_router)
api_router.include_router(partner_router)
api_router.include_router(b2b_router)
api_router.include_router(system_backup_router)
