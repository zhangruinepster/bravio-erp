import os
import sys
import logging
from collections import deque
from typing import List, Dict, Any
from loguru import logger
from app.core.config import settings

# 在 Windows 下确保 stdout/stderr 编码支持 UTF-8
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 内存日志环形缓冲区（最多保留最近 500 条日志，供前端实时开发监控面板展示）
MAX_MEMORY_LOGS = 500
memory_log_buffer: deque = deque(maxlen=MAX_MEMORY_LOGS)

class InterceptHandler(logging.Handler):
    """
    拦截 Python 标准 logging 库的日志并重定向到 Loguru
    使 uvicorn, fastapi, sqlalchemy 的日志统一格式输出
    """
    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def memory_log_sink(message):
    """
    将日志存入内存缓冲队列，供前端开发者面板调取
    """
    record = message.record
    log_entry = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "line": record["line"],
        "function": record["function"],
        "extra": record.get("extra", {})
    }
    memory_log_buffer.append(log_entry)

def setup_logger():
    """
    初始化开发者日志系统
    - 屏幕输出（彩色高亮，UTF-8）
    - 文件输出（轮转归档，带 requestId 与行号追踪）
    - 内存缓冲区（前端实时调试）
    """
    # 确保日志目录存在
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # 移除 loguru 默认 handler
    logger.remove()

    # 1. 控制台彩色高亮输出
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # 2. 开发者日志文件轮转存储 (按天轮转, 最多保留 14 天)
    file_log_path = os.path.join(settings.LOG_DIR, "bravio_dev_{time:YYYY-MM-DD}.log")
    logger.add(
        file_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="00:00",
        retention="14 days",
        compression="zip",
        encoding="utf-8"
    )

    # 3. 内存 Sink (供开发者调试面板调取)
    logger.add(memory_log_sink, level="DEBUG")

    # 4. 拦截标准库 logging
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    logger.info("[INIT] Bravio ERP 开发者日志系统就绪 [Level: {}, Dir: {}]", settings.LOG_LEVEL, settings.LOG_DIR)
    return logger

def get_recent_dev_logs(limit: int = 100, level: str = None) -> List[Dict[str, Any]]:
    """
    获取最近的开发者日志
    """
    logs = list(memory_log_buffer)
    if level:
        level_upper = level.upper()
        logs = [log for log in logs if log["level"] == level_upper]
    return logs[-limit:]
