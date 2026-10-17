from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.logger import logger

class ERPException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str = "ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code

async def erp_exception_handler(request: Request, exc: ERPException):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.warning(f"[{request_id}] ERPException: [{exc.code}] {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.detail,
            "request_id": request_id
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.exception(f"[{request_id}] Unhandled Server Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "系统内部异常，请联系管理员或查看开发者日志",
            "request_id": request_id
        }
    )
