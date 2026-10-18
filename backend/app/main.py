import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logger import setup_logger, logger
from app.core.database import init_db
from app.core.init_data import seed_initial_data
from app.core.middlewares import RequestTraceMiddleware
from app.core.exceptions import ERPException, erp_exception_handler, global_exception_handler
from app.api.v1.api import api_router

# 初始化系统日志
setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动前执行
    logger.info("[START] 正在启动 Bravio ERP 服务集群...")
    await init_db()
    await seed_initial_data()
    logger.info(f"[READY] Bravio ERP 服务集群已就绪 - 环境: {settings.ENVIRONMENT}, 版本: {settings.VERSION}")
    yield
    # 服务停止后执行
    logger.info("[SHUTDOWN] Bravio ERP 服务集群平稳停止")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="企业级模块化 ERP 系统 - 数字化智能中枢",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 1. 跨域 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 请求全链路日志与性能追踪中间件
app.add_middleware(RequestTraceMiddleware)

# 开发热更新防浏览器强缓存中间件
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or any(path.endswith(ext) for ext in (".js", ".css", ".html")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# 3. 异常处理器
app.add_exception_handler(ERPException, erp_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 4. 注册 API 核心路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 5. 静态资源与前端门户 UI 挂载
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
static_dir = os.path.join(os.path.dirname(__file__), "static")

# 挂载上传文件存储卷与多媒体目录
upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(upload_dir, exist_ok=True)
os.makedirs(os.path.join(upload_dir, "demo"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if os.path.exists(frontend_dir):
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    assets_dir = os.path.join(frontend_dir, "assets")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="frontend-css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="frontend-js")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def serve_portal():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
elif os.path.exists(static_dir):
    @app.get("/", include_in_schema=False)
    async def serve_portal_static():
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "system": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": f"{settings.API_V1_STR}/docs"
        }

