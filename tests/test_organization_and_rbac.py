import pytest
import os
import sys
from datetime import datetime, timezone, timedelta

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

async def get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.INITIAL_SUPERUSER_USERNAME,
            "password": settings.INITIAL_SUPERUSER_PASSWORD
        }
    )
    assert resp.status_code == 200
    return resp.json()["token"]["access_token"]

async def get_operator_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "operator",
            "password": "operator123"
        }
    )
    assert resp.status_code == 200
    return resp.json()["token"]["access_token"]

@pytest.mark.asyncio
async def test_rbac_permissions_and_roles():
    """测试系统权限清单与角色矩阵查询"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 查询所有注册的权限项
        perm_res = await client.get("/api/v1/rbac/permissions", headers=headers)
        assert perm_res.status_code == 200
        perms = perm_res.json()
        assert len(perms) >= 15
        codes = [p["code"] for p in perms]
        assert "hr.department.create" in codes
        assert "kba.cop.audit" in codes

        # 2. 查询角色矩阵
        role_res = await client.get("/api/v1/rbac/roles", headers=headers)
        assert role_res.status_code == 200
        roles = role_res.json()
        role_codes = [r["code"] for r in roles]
        assert "ROLE_SUPER_ADMIN" in role_codes
        assert "ROLE_QUALITY_HEAD" in role_codes

@pytest.mark.asyncio
async def test_department_tree_and_hierarchy():
    """测试组织架构树查询与自引用层级"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/org/departments/tree", headers=headers)
        assert resp.status_code == 200
        tree = resp.json()
        assert len(tree) >= 1
        hq_node = next((n for n in tree if n["code"] == "DEPT-HQ"), None)
        assert hq_node is not None
        assert len(hq_node["children"]) >= 3 # 质保、制造、研发
        child_codes = [c["code"] for c in hq_node["children"]]
        assert "DEPT-QA" in child_codes
        assert "DEPT-MFG" in child_codes

@pytest.mark.asyncio
async def test_job_positions_and_safety_critical():
    """测试特殊特性关键岗位标识与资质要求"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/org/positions", headers=headers)
        assert resp.status_code == 200
        positions = resp.json()
        kba_pos = next((p for p in positions if p["code"] == "POS-KBA-SPEC"), None)
        assert kba_pos is not None
        assert kba_pos["is_safety_critical"] is True
        assert "KBA_COP_LEAD_AUDITOR" in kba_pos["required_cert_types"]

@pytest.mark.asyncio
async def test_employee_competency_audit_and_warning():
    """测试 KBA/ISO 关键工位资质自动审查与到期预警机制"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/org/employees", headers=headers)
        assert resp.status_code == 200
        employees = resp.json()
        zhang = next((e for e in employees if e["employee_no"] == "BR-2026-001"), None)
        assert zhang is not None
        assert zhang["department_name"] is not None
        assert len(zhang["certifications"]) >= 2

        # 检查关键岗位资质合规结论
        comp = zhang["competency_status"]
        assert comp["is_safety_critical_job"] is True
        assert comp["is_compliant"] is True
        # 预警列表中应捕捉到20天内到期的 ISO9001 证书
        assert len(comp["warning_cert_types"]) >= 1

@pytest.mark.asyncio
async def test_expiring_certifications_dashboard():
    """测试 30 天内到期资质预警查询接口"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/org/certifications/expiring?days=30", headers=headers)
        assert resp.status_code == 200
        expiring = resp.json()
        assert len(expiring) >= 1
        cert_types = [c["cert_type"] for c in expiring]
        assert "ISO9001_LEAD_AUDITOR" in cert_types

@pytest.mark.asyncio
async def test_operator_permission_boundary():
    """测试普通操作员越权创建部门时被 RBAC 守卫 403 阻断"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        op_token = await get_operator_token(client)
        headers = {"Authorization": f"Bearer {op_token}"}

        resp = await client.post(
            "/api/v1/org/departments",
            json={
                "code": "DEPT-HACK",
                "name": "越权伪造部门",
                "iso_process_type": "CORE"
            },
            headers=headers
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "操作权限不足" in data["detail"]
