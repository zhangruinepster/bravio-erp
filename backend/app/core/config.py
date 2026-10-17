from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bravio ERP"
    VERSION: str = "0.1.0-dev"
    API_V1_STR: str = "/api/v1"

    
    # 运行环境: development, testing, production
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 安全密钥与 JWT
    SECRET_KEY: str = "bravio-erp-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 开发模式下默认 24 小时
    
    # 数据库连接 (本地默认 sqlite 异步, 容器化可配置 postgresql+asyncpg)
    DATABASE_URL: str = "sqlite+aiosqlite:///./erp_dev.db"
    
    # Redis 缓存连接 (可选)
    REDIS_URL: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    
    # CORS 白名单
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 初始化预设超级管理员
    INITIAL_SUPERUSER_EMAIL: str = "admin@bravio-erp.com"
    INITIAL_SUPERUSER_USERNAME: str = "admin"
    INITIAL_SUPERUSER_PASSWORD: str = "admin123"
    INITIAL_SUPERUSER_NAME: str = "系统总管理员"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
