from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logger import logger

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取数据库会话并在结束时自动关闭"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session rollback due to exception: {}", e)
            raise
        finally:
            await session.close()

async def init_db():
    """初始化数据库表结构与默认数据"""
    async with engine.begin() as conn:
        logger.info("Initializing database schema...")
        await conn.run_sync(Base.metadata.create_all)
        # 兼容性无损平滑迁移：若为 sqlite 且新增了列，自动安全补偿 ALTER TABLE
        if settings.DATABASE_URL.startswith("sqlite"):
            from sqlalchemy import text
            try:
                await conn.execute(text("ALTER TABLE hr_employees ADD COLUMN avatar_url VARCHAR(500)"))
            except Exception:
                pass  # 列已存在
    logger.info("Database schema initialized successfully.")
