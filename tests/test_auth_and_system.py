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
    """测试开发者日志实时读取与触发"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 触发测试日志
        emit_res = await client.post(
            "/api/v1/system/logs/test",
            params={"level": "WARNING", "message": "Automated Test Log Message"}
        )
        assert emit_res.status_code == 200

        # 2. 读取最近日志
        logs_res = await client.get("/api/v1/system/logs?limit=10")
        assert logs_res.status_code == 200
        logs_data = logs_res.json()
        assert "logs" in logs_data
        assert len(logs_data["logs"]) > 0
        messages = [log["message"] for log in logs_data["logs"]]
        assert any("Automated Test Log Message" in msg for msg in messages)
