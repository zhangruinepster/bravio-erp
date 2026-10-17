import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.logger import logger, get_recent_dev_logs, memory_log_buffer
from app.core.database import get_db
from app.schemas.system import HealthCheckResponse, DevLogsResponse

router = APIRouter(prefix="/system", tags=["系统监控与开发者工具"])

APP_START_TIME = time.time()

@router.get("/health", response_model=HealthCheckResponse, summary="系统健康探针")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    检查系统健康状况及核心依赖可用性（数据库连接、运行时间）
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Health check database failure: {e}")

    uptime = time.time() - APP_START_TIME

    return HealthCheckResponse(
        status="operational" if db_status == "connected" else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/logs", response_model=DevLogsResponse, summary="开发者实时日志获取")
async def get_developer_logs(
    limit: int = Query(50, ge=1, le=500, description="获取条数"),
    level: Optional[str] = Query(None, description="过滤级别: DEBUG, INFO, WARNING, ERROR")
):
    """
    供开发者前端工作台直接查看后端实时运行日志（无需登录服务器或切到终端）
    """
    logs = get_recent_dev_logs(limit=limit, level=level)
    return DevLogsResponse(
        total_logs_in_memory=len(memory_log_buffer),
        returned_count=len(logs),
        logs=logs
    )

@router.post("/logs/test", summary="触发测试日志（供开发者联调）")
async def emit_test_log(
    level: str = Query("INFO", description="测试日志级别: DEBUG, INFO, WARNING, ERROR"),
    message: str = Query("开发者手动触发测试日志", description="日志消息"),
    request: Request = None
):
    """
    测试开发者日志捕获与输出管道
    """
    req_id = getattr(request.state, "request_id", "manual") if request else "manual"
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{req_id}] 🧪 [DEV_TEST_LOG] {message}")
    return {"success": True, "message": f"已成功向系统日志系统投递一条 {level} 级别日志"}
