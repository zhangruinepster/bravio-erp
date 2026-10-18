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

async def get_pe_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "pe",
            "password": "pe123"
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
async def test_pe_permission_boundary():
    """测试产品工程师越权创建组织部门时被 RBAC 守卫 403 阻断"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pe_token = await get_pe_token(client)
        headers = {"Authorization": f"Bearer {pe_token}"}

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

@pytest.mark.asyncio
async def test_real_hr_accounts_and_roles_matrix():
    """测试 V0.1 五大真实人事账号 (GM, PE, QE, Supplier, Admin) 登录与人事档案角色绑定，验证车间质检员已彻底删除"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 验证旧的车间质检员 operator 账号已被彻底清除
        op_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "operator", "password": "operator123"}
        )
        assert op_res.status_code == 401

        # 2. 验证总经理 (gm) 登录
        gm_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "gm", "password": "gm123"}
        )
        assert gm_res.status_code == 200
        gm_user = gm_res.json()["user"]
        assert gm_user["username"] == "gm"
        assert gm_user["is_superuser"] is False
        assert "陈总裁" in gm_user["full_name"]

        # 3. 验证产品工程师 (pe) 登录
        pe_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "pe", "password": "pe123"}
        )
        assert pe_res.status_code == 200
        pe_user = pe_res.json()["user"]
        assert pe_user["username"] == "pe"
        assert "王工程" in pe_user["full_name"]

        # 4. 验证质量工程师 (qe) 登录
        qe_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "qe", "password": "qe123"}
        )
        assert qe_res.status_code == 200
        qe_user = qe_res.json()["user"]
        assert qe_user["username"] == "qe"
        assert "刘质保" in qe_user["full_name"]

        # 5. 验证供应商账户 (supplier) 登录
        sup_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "supplier", "password": "supplier123"}
        )
        assert sup_res.status_code == 200
        sup_user = sup_res.json()["user"]
        assert sup_user["username"] == "supplier"
        assert "张供应" in sup_user["full_name"]

        # 6. 管理员登录并拉取员工花名册，验证真实人事档案及绑定的 RBAC 角色
        admin_token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {admin_token}"}
        emp_res = await client.get("/api/v1/org/employees", headers=headers)
        assert emp_res.status_code == 200
        employees = emp_res.json()

        # 6.1 验证不存在车间质检员
        assert not any(e["employee_no"] == "BR-2026-OP" for e in employees)

        # 6.2 验证总经理人事档案
        emp_gm = next(e for e in employees if e["employee_no"] == "BR-2026-000")
        assert emp_gm["account_username"] == "gm"
        assert "集团总经理" in emp_gm["account_roles"]
        assert emp_gm["department_name"] == "Bravio 集团总部"

        # 6.3 验证产品工程师人事档案
        emp_pe = next(e for e in employees if e["employee_no"] == "BR-2026-101")
        assert emp_pe["account_username"] == "pe"
        assert "产品工程师" in emp_pe["account_roles"]
        assert "研发与工程技术中心" in emp_pe["department_name"]

        # 6.4 验证质量工程师人事档案
        emp_qe = next(e for e in employees if e["employee_no"] == "BR-2026-201")
        assert emp_qe["account_username"] == "qe"
        assert "质量工程师" in emp_qe["account_roles"]
        assert "质量保证与法规合规中心" in emp_qe["department_name"]
        assert len(emp_qe["certifications"]) >= 1

        # 6.5 验证供应商专员人事档案
        emp_sup = next(e for e in employees if e["employee_no"] == "BR-2026-301")
        assert emp_sup["account_username"] == "supplier"
        assert "供应商专员" in emp_sup["account_roles"]
        assert "先进制造与供应链中心" in emp_sup["department_name"]

@pytest.mark.asyncio
async def test_create_employee_with_user_account():
    """测试录入新员工时同步创建登录账号密码并完成首次认证闭环"""
    import uuid
    uid = uuid.uuid4().hex[:6]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 获取质保部门和产品工程师角色 ID
        depts_res = await client.get("/api/v1/org/departments", headers=headers)
        qa_dept_id = depts_res.json()[0]["id"]

        roles_res = await client.get("/api/v1/rbac/roles", headers=headers)
        pe_role = next(r for r in roles_res.json() if r["code"] == "ROLE_PRODUCT_ENGINEER")

        # 录入员工并开设账号
        emp_payload = {
            "employee_no": f"BR-TEST-{uid}",
            "name": f"测试员工-{uid}",
            "email": f"test_{uid}@bravio-erp.com",
            "phone": "+86 13800000000",
            "department_id": qa_dept_id,
            "status": "ACTIVE",
            "account": {
                "username": f"user_{uid}",
                "password": "Password123!",
                "role_ids": [pe_role["id"]],
                "is_active": True
            }
        }

        create_res = await client.post("/api/v1/org/employees", json=emp_payload, headers=headers)
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["employee_no"] == f"BR-TEST-{uid}"
        assert data["account_username"] == f"user_{uid}"
        assert pe_role["name"] in data["account_roles"]

        # 验证新开设的员工账号可成功登录并生成 Token
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": f"user_{uid}", "password": "Password123!"}
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_data["success"] is True
        assert login_data["user"]["username"] == f"user_{uid}"
        new_token = login_data["token"]["access_token"]

        # 验证新用户携带 Token 可访问 /auth/me
        me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert me_res.status_code == 200
        assert me_res.json()["username"] == f"user_{uid}"

