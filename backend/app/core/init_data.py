from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.logger import logger
from app.models.user import User

async def seed_initial_data():
    """初始化预设账号与基础角色种子数据"""
    async with AsyncSessionLocal() as db:
        # 1. 检查超级管理员是否存在
        stmt = select(User).where(User.username == settings.INITIAL_SUPERUSER_USERNAME)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username=settings.INITIAL_SUPERUSER_USERNAME,
                email=settings.INITIAL_SUPERUSER_EMAIL,
                full_name=settings.INITIAL_SUPERUSER_NAME,
                hashed_password=get_password_hash(settings.INITIAL_SUPERUSER_PASSWORD),
                role="admin",
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            logger.info(
                f"[SEED] 已创建默认超级管理员: 用户名 '{settings.INITIAL_SUPERUSER_USERNAME}' / 密码 '{settings.INITIAL_SUPERUSER_PASSWORD}'"
            )

        # 2. 检查演示操作员账号
        stmt_op = select(User).where(User.username == "operator")
        result_op = await db.execute(stmt_op)
        operator = result_op.scalar_one_or_none()

        if not operator:
            operator = User(
                username="operator",
                email="operator@bravio-erp.com",
                full_name="车间质检操作员",
                hashed_password=get_password_hash("operator123"),
                role="operator",
                is_active=True,
                is_superuser=False
            )
            db.add(operator)
            logger.info("[SEED] 已创建默认演示操作员: 用户名 'operator' / 密码 'operator123'")

        await db.commit()
