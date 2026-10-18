import pytest
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_v031_partner_lifecycle():
    """测试 V0.3.1 商业伙伴创建、详情读取与更新保存完整闭环"""
    unique_code = f"SUP-MUC-{uuid.uuid4().hex[:4].upper()}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 登录管理员
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": settings.INITIAL_SUPERUSER_USERNAME, "password": settings.INITIAL_SUPERUSER_PASSWORD}
        )
        token = login_res.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 登记新商业伙伴
        create_res = await client.post(
            "/api/v1/partners",
            json={
                "partner_code": unique_code,
                "name": "慕尼黑光电协同测试代工厂",
                "partner_type": "SUPPLIER",
                "contact_person": "Hans Weber",
                "contact_email": "weber@muc-test.de",
                "contact_phone": "+49 89 99887766",
                "is_oem_certified": True,
                "payment_terms_days": 45,
                "shipping_address": "Munich Logistics Center Gate 1",
                "notes": "V0.3.1 自动化测试测试专用伙伴"
            },
            headers=headers
        )
        assert create_res.status_code == 201
        p_data = create_res.json()
        partner_id = p_data["id"]
        assert p_data["partner_code"] == unique_code
        assert p_data["api_token"].startswith("m2m_")

        # 3. 读取单个商业伙伴详情
        get_res = await client.get(f"/api/v1/partners/{partner_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "慕尼黑光电协同测试代工厂"

        # 4. 修改保存商业伙伴
        update_res = await client.put(
            f"/api/v1/partners/{partner_id}",
            json={
                "name": "慕尼黑光电协同制造总装股份公司 (更新)",
                "contact_person": "Hans Weber Jr.",
                "payment_terms_days": 90,
                "is_active": True
            },
            headers=headers
        )
        assert update_res.status_code == 200
        up_data = update_res.json()
        assert up_data["name"] == "慕尼黑光电协同制造总装股份公司 (更新)"
        assert up_data["payment_terms_days"] == 90
        assert up_data["contact_person"] == "Hans Weber Jr."


import uuid

@pytest.mark.asyncio
async def test_v031_product_lifecycle():
    """测试 V0.3.1 产品料号定义、详情穿透与工程维护闭环"""
    unique_suffix = uuid.uuid4().hex[:4].upper()
    unique_bravio_id = f"8{unique_suffix}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": settings.INITIAL_SUPERUSER_USERNAME, "password": settings.INITIAL_SUPERUSER_PASSWORD}
        )
        token = login_res.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 定义新产品料号
        create_res = await client.post(
            "/api/v1/products",
            json={
                "bravio_id": unique_bravio_id,
                "product_name": "Matrix LED 智能激光大灯总成 36W",
                "current_revision": "A",
                "category": "HEADLIGHT",
                "is_certified": True,
                "kba_approval_number": "E1-149R-009988",
                "homologation_authority": "KBA-Flensburg",
                "iso_classification": "SAFETY_RELEVANT",
                "is_serialized": True,
                "standard_warranty_months": 36,
                "lifecycle_status": "PROJECT_KICKOFF",
                "current_phase_gate": 1,
                "notes": "V0.3.1 测试料号"
            },
            headers=headers
        )
        assert create_res.status_code == 201
        prod_data = create_res.json()
        prod_id = prod_data["id"]
        assert prod_data["bravio_id"] == unique_bravio_id

        # 2. 读取产品详情
        get_res = await client.get(f"/api/v1/products/{prod_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["product_name"] == "Matrix LED 智能激光大灯总成 36W"

        # 3. 修改保存产品
        update_res = await client.put(
            f"/api/v1/products/{prod_id}",
            json={
                "product_name": "Matrix LED 智能激光大灯总成 36W (工程升级版)",
                "current_revision": "B",
                "current_phase_gate": 2,
                "lifecycle_status": "A_SAMPLE"
            },
            headers=headers
        )
        assert update_res.status_code == 200
        up_data = update_res.json()
        assert up_data["current_revision"] == "B"
        assert up_data["product_name"] == "Matrix LED 智能激光大灯总成 36W (工程升级版)"
        assert up_data["current_phase_gate"] == 2
        assert up_data["lifecycle_status"] == "A_SAMPLE"


@pytest.mark.asyncio
async def test_v031_employee_detail_and_update():
    """测试 V0.3.1 员工详情与档案修改保存"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": settings.INITIAL_SUPERUSER_USERNAME, "password": settings.INITIAL_SUPERUSER_PASSWORD}
        )
        token = login_res.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 查询员工列表取第一个
        emps_res = await client.get("/api/v1/org/employees", headers=headers)
        assert emps_res.status_code == 200
        emps = emps_res.json()
        assert len(emps) > 0
        target_emp = emps[0]

        # 2. 获取单个员工详情
        get_res = await client.get(f"/api/v1/org/employees/{target_emp['id']}", headers=headers)
        assert get_res.status_code == 200
        detail = get_res.json()
        assert detail["id"] == target_emp["id"]
        assert "competency_status" in detail

        # 3. 修改保存员工信息
        new_phone = "+49 89 88880000"
        up_res = await client.put(
            f"/api/v1/org/employees/{target_emp['id']}",
            json={"phone": new_phone},
            headers=headers
        )
        assert up_res.status_code == 200
        assert up_res.json()["phone"] == new_phone
