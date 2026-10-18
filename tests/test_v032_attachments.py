import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_v032_attachment_upload_and_management():
    """测试 v0.3.2 附件上传、SHA256哈希防篡改计算、绑定与生命周期管理"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 登录管理员获取凭证
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": settings.INITIAL_SUPERUSER_PASSWORD}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 获取测试员工
        emp_res = await client.get("/api/v1/org/employees", headers=headers)
        assert emp_res.status_code == 200
        emps = emp_res.json()
        assert len(emps) > 0
        test_emp_id = emps[0]["id"]

        # 3. 上传员工头像
        file_content = b"<svg xmlns='http://www.w3.org/2000/svg'><circle r='10'/></svg>"
        files = {"file": ("test_avatar.svg", io.BytesIO(file_content), "image/svg+xml")}
        data = {
            "res_model": "hr_employee",
            "res_id": test_emp_id,
            "description": "单元测试头像上传"
        }
        up_res = await client.post(
            "/api/v1/system/attachments/upload",
            headers=headers,
            data=data,
            files=files
        )
        assert up_res.status_code == 200
        att_data = up_res.json()
        assert att_data["res_model"] == "hr_employee"
        assert att_data["res_id"] == test_emp_id
        assert len(att_data["sha256_hash"]) == 64
        att_id = att_data["id"]

        # 4. 验证员工档案已被自动双向更新
        emp_detail = await client.get(f"/api/v1/org/employees/{test_emp_id}", headers=headers)
        assert emp_detail.status_code == 200
        assert emp_detail.json()["avatar_url"] == att_data["file_url"]

        # 5. 测试一键绑定 Demo 素材至产品
        prod_res = await client.get("/api/v1/products", headers=headers)
        assert prod_res.status_code == 200
        prods = prod_res.json()
        assert len(prods) > 0
        test_prod_id = prods[0]["id"]

        bind_res = await client.post(
            "/api/v1/system/attachments/bind-demo",
            headers=headers,
            json={
                "res_model": "product_master",
                "res_id": test_prod_id,
                "demo_filename": "product_matrix_led.svg",
                "description": "绑定矩阵大灯 Demo 渲染图"
            }
        )
        assert bind_res.status_code == 200
        assert bind_res.json()["res_model"] == "product_master"

        # 6. 获取全局附件列表与存储统计
        stats_res = await client.get("/api/v1/system/attachments/stats", headers=headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_count"] >= 2
        assert "hr_employee" in stats["model_breakdown"]

        list_res = await client.get("/api/v1/system/attachments", headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 2

        # 7. 删除刚刚测试创建的附件
        del_res = await client.delete(f"/api/v1/system/attachments/{att_id}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True
