import os
import sys
import pytest
import pytest_asyncio

# 加入 backend 路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import init_db
from app.core.init_data import seed_initial_data

@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """测试开始前初始化数据库和种子数据"""
    await init_db()
    await seed_initial_data()
    yield
