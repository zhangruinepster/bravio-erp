from fastapi import APIRouter
from app.api.v1.endpoints import auth, system, organization, rbac

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(system.router)
api_router.include_router(rbac.router, prefix="/rbac", tags=["权限与角色控制中心"])
api_router.include_router(organization.router, prefix="/org", tags=["组织架构与人员资质合规"])


