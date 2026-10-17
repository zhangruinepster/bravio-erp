import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logger import logger

class RequestTraceMiddleware(BaseHTTPMiddleware):
    """
    请求追踪中间件：
    - 注入全局唯一 X-Request-Id
    - 记录 API 耗时与状态码
    - 输出结构化访问日志
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        logger.debug(f"[{request_id}] -> {method} {path} from {client_ip}")

        try:
            response: Response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            log_level = logger.info if response.status_code < 400 else logger.warning
            log_level(
                f"[{request_id}] <- {method} {path} {response.status_code} "
                f"({process_time:.2f}ms)"
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.exception(
                f"[{request_id}] !! {method} {path} ERROR: {exc} ({process_time:.2f}ms)"
            )
            raise exc
