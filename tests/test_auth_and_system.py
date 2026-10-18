import pytest
import os
import sys

# 将 backend 加入 python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_health_check():
    """测试系统健康探针接口"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("operational", "degraded")
        assert data["version"] == settings.VERSION

@pytest.mark.asyncio
async def test_admin_login_success():
    """测试超级管理员账号默认密码登录"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.INITIAL_SUPERUSER_USERNAME,
                "password": settings.INITIAL_SUPERUSER_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert "access_token" in data["token"]
        assert data["user"]["username"] == settings.INITIAL_SUPERUSER_USERNAME
        assert data["user"]["role"] == "admin"

@pytest.mark.asyncio
async def test_login_invalid_password():
    """测试错误密码拦截与 401 响应"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrong_password_123"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

@pytest.mark.asyncio
async def test_get_current_user_me():
    """测试基于 JWT 获取当前用户信息"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 先登录
        login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.INITIAL_SUPERUSER_USERNAME,
                "password": settings.INITIAL_SUPERUSER_PASSWORD
            }
        )
        token = login_res.json()["token"]["access_token"]

        # 调取 /auth/me
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        user_data = me_res.json()
        assert user_data["username"] == settings.INITIAL_SUPERUSER_USERNAME

@pytest.mark.asyncio
async def test_developer_logs_system():
    """测试系统管理员可读取开发者日志，而总经理(gm)被 403 严格阻断"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 管理员登录
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.INITIAL_SUPERUSER_USERNAME,
                "password": settings.INITIAL_SUPERUSER_PASSWORD
            }
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. 管理员触发测试日志
        emit_res = await client.post(
            "/api/v1/system/logs/test",
            params={"level": "WARNING", "message": "Automated Test Log Message"},
            headers=admin_headers
        )
        assert emit_res.status_code == 200

        # 3. 管理员读取最近日志
        logs_res = await client.get("/api/v1/system/logs?limit=10", headers=admin_headers)
        assert logs_res.status_code == 200
        logs_data = logs_res.json()
        assert "logs" in logs_data
        assert len(logs_data["logs"]) > 0

        # 4. 总经理登录
        gm_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "gm", "password": "gm123"}
        )
        assert gm_login.status_code == 200
        gm_token = gm_login.json()["token"]["access_token"]
        gm_headers = {"Authorization": f"Bearer {gm_token}"}

        # 5. 总经理尝试访问开发者日志 -> 必须被 403 严格阻断！
        gm_logs_res = await client.get("/api/v1/system/logs", headers=gm_headers)
        assert gm_logs_res.status_code == 403
        assert "需要系统管理员权限" in gm_logs_res.json()["detail"]


@pytest.mark.asyncio
async def test_database_inspector_preview():
    """测试数据库内容预览探针：管理员全权检视，非管理员严格 403 阻断"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 管理员登录
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.INITIAL_SUPERUSER_USERNAME,
                "password": settings.INITIAL_SUPERUSER_PASSWORD
            }
        )
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. 读取全量数据库表列表
        tables_res = await client.get("/api/v1/system/db/tables", headers=admin_headers)
        assert tables_res.status_code == 200
        tables_data = tables_res.json()
        assert tables_data["total_tables"] >= 20
        assert any(t["table_name"] == "sys_users" for t in tables_data["tables"])

        # 3. 读取 sys_users 数据
        users_data_res = await client.get("/api/v1/system/db/tables/sys_users/data?page=1&page_size=10", headers=admin_headers)
        assert users_data_res.status_code == 200
        users_table = users_data_res.json()
        assert users_table["total_rows"] >= 1
        assert len(users_table["rows"]) >= 1
        # 验证密码已脱敏保护
        first_user = users_table["rows"][0]
        assert "●●●●●●" in first_user["hashed_password"]

        # 4. 总经理访问数据库探针 -> 必须被 403 严格阻断
        gm_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "gm", "password": "gm123"}
        )
        gm_token = gm_login.json()["token"]["access_token"]
        gm_headers = {"Authorization": f"Bearer {gm_token}"}

        gm_tables_res = await client.get("/api/v1/system/db/tables", headers=gm_headers)
        assert gm_tables_res.status_code == 403

