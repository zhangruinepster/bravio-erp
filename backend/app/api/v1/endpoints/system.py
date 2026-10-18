import os
import hashlib
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, desc, delete

from app.core.config import settings
from app.core.logger import logger, get_recent_dev_logs, memory_log_buffer
from app.core.database import get_db
from app.schemas.system import HealthCheckResponse, DevLogsResponse
from app.schemas.attachment import AttachmentResponse, AttachmentStatsResponse
from app.api.deps import get_current_superuser, get_current_user
from app.models.user import User
from app.models.attachment import SystemAttachment
from app.models.organization import Employee
from app.modules.product.models import ProductMaster

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
    level: Optional[str] = Query(None, description="过滤级别: DEBUG, INFO, WARNING, ERROR"),
    current_user: User = Depends(get_current_superuser)
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
    request: Request = None,
    current_user: User = Depends(get_current_superuser)
):
    """
    测试开发者日志捕获与输出管道
    """
    req_id = getattr(request.state, "request_id", "manual") if request else "manual"
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{req_id}] 🧪 [DEV_TEST_LOG] {message}")
    return {"success": True, "message": f"已成功向系统日志系统投递一条 {level} 级别日志"}

# =========================================================================
# 数据库全景与内容探针 (Database Inspector - docs/05)
# =========================================================================

TABLE_METADATA_MAP = {
    "sys_users": {"display_name": "系统用户档案与身份凭据", "category": "🛠️ 核心架构与RBAC"},
    "sys_roles": {"display_name": "系统角色与数据范围定义", "category": "🛠️ 核心架构与RBAC"},
    "sys_permissions": {"display_name": "功能权限项总览 (RBAC)", "category": "🛠️ 核心架构与RBAC"},
    "sys_user_roles": {"display_name": "用户与系统角色分配映射", "category": "🛠️ 核心架构与RBAC"},
    "sys_role_permissions": {"display_name": "角色持有的细粒度权限映射", "category": "🛠️ 核心架构与RBAC"},
    "sys_audit_logs": {"display_name": "ISO 9001 不可篡改审计日志", "category": "🛠️ 核心架构与RBAC"},
    "backup_records": {"display_name": "数据库快照与 SHA-256 校验包", "category": "💾 容灾备份与安全回滚"},
    "hr_departments": {"display_name": "集团多级组织架构树 (ISO分类)", "category": "👥 人事实体与合规资质"},
    "hr_job_positions": {"display_name": "企业工位目录与特殊特性要求", "category": "👥 人事实体与合规资质"},
    "hr_employees": {"display_name": "员工人事花名册档案", "category": "👥 人事实体与合规资质"},
    "hr_employee_certifications": {"display_name": "KBA/ISO 关键工位资质证书", "category": "👥 人事实体与合规资质"},
    "hr_employee_trainings": {"display_name": "员工技术培训履历与评价", "category": "👥 人事实体与合规资质"},
    "product_masters": {"display_name": "车规级产品主数据与APQP阶段门", "category": "📐 研发物料与多级BOM"},
    "boms": {"display_name": "工程物料清单版本 (BOM Master)", "category": "📐 研发物料与多级BOM"},
    "bom_items": {"display_name": "多级工程 BOM 子部件组成项", "category": "📐 研发物料与多级BOM"},
    "packaging_hierarchies": {"display_name": "出货包装层级规范 (盒/箱/托)", "category": "📐 研发物料与多级BOM"},
    "engineering_change_orders": {"display_name": "汽车级工程变更控制 (ECR/ECO/ECN)", "category": "📋 汽车工程变更 (ECM)"},
    "barcode_rules": {"display_name": "多层级动态条码编码规则引擎", "category": "🏷️ 规则引擎与条码模板"},
    "laser_serial_codes": {"display_name": "32位激光防伪微距码物化库", "category": "⚡ 32位激光防伪与防呆"},
    "pairing_records": {"display_name": "一盒双灯同Bin防呆配对流水", "category": "⚡ 32位激光防伪与防呆"},
    "packaging_units": {"display_name": "四级包装树实体 (SN/BOX/CTN/PLT)", "category": "📦 四级包装树与逆向售后"},
    "rma_orders": {"display_name": "逆向售后 RMA 与调包风控单", "category": "📦 四级包装树与逆向售后"},
    "inspection_sheets": {"display_name": "进料/过程/出厂检验质检单", "category": "🛡️ 质量检验与受控文档"},
    "eight_d_incidents": {"display_name": "8D 质量客诉事故闭环攻关单", "category": "🛡️ 质量检验与受控文档"},
    "controlled_documents": {"display_name": "ISO 9001 四层金字塔受控文档", "category": "🛡️ 质量检验与受控文档"},
    "business_partners": {"display_name": "商业伙伴通用档案 (供应商/客户)", "category": "🏭 商业伙伴与外协协同"},
    "b2b_work_orders": {"display_name": "B2B 外协代工任务与条码预分配", "category": "🏭 商业伙伴与外协协同"},
    "sys_attachments": {"display_name": "系统受控附件与多媒体资产库", "category": "📁 全局附件与多媒体"},
}

@router.get("/db/tables", summary="获取数据库全量数据表元数据与行数概览")
async def get_db_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    系统总管理员独占：读取数据库全量持久化数据表列表、结构定义与行数统计
    """
    from sqlalchemy import inspect
    
    def _inspect_tables(sync_conn):
        insp = inspect(sync_conn)
        return insp.get_table_names()

    table_names = await db.run_sync(lambda s: inspect(s.bind).get_table_names())
    
    tables_result = []
    total_db_records = 0

    for tbl in sorted(table_names):
        # 统计行数
        try:
            cnt_res = await db.execute(text(f'SELECT COUNT(*) FROM "{tbl}"'))
            row_count = cnt_res.scalar() or 0
        except Exception:
            row_count = 0
        total_db_records += row_count

        meta = TABLE_METADATA_MAP.get(tbl, {"display_name": tbl, "category": "📦 其他业务数据"})

        def _get_cols(s):
            insp = inspect(s.bind)
            raw_cols = insp.get_columns(tbl)
            return [
                {
                    "name": c["name"],
                    "type": str(c["type"]),
                    "nullable": c.get("nullable", True),
                    "primary_key": bool(c.get("primary_key", False))
                }
                for c in raw_cols
            ]

        col_defs = await db.run_sync(_get_cols)

        tables_result.append({
            "table_name": tbl,
            "display_name": meta["display_name"],
            "category": meta["category"],
            "row_count": row_count,
            "column_count": len(col_defs),
            "columns": col_defs
        })

    return {
        "total_tables": len(tables_result),
        "total_records": total_db_records,
        "database_engine": "PostgreSQL 16 / SQLite ACID",
        "tables": tables_result
    }

@router.get("/db/tables/{table_name}/data", summary="分页读取指定数据表内容")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页行数"),
    search: Optional[str] = Query(None, description="全文关键字检索"),
    sort_by: Optional[str] = Query(None, description="排序列名"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    系统总管理员独占：安全读取单表行级数据（防 SQL 注入，密码字段自动脱敏）
    """
    from sqlalchemy import inspect
    from fastapi import HTTPException
    import math

    # 1. 强安全校验：表名必须存在于系统元数据中
    table_names = await db.run_sync(lambda s: inspect(s.bind).get_table_names())
    if table_name not in table_names:
        raise HTTPException(status_code=404, detail=f"数据表 '{table_name}' 不存在")

    # 2. 列元数据
    def _inspect_col(s):
        insp = inspect(s.bind)
        return insp.get_columns(table_name)
    cols = await db.run_sync(_inspect_col)
    col_names = [c["name"] for c in cols]
    col_map = {c["name"]: str(c["type"]) for c in cols}

    # 3. 排序安全性检查
    order_clause = ""
    if sort_by:
        if sort_by not in col_names:
            raise HTTPException(status_code=400, detail=f"无效的排序列: {sort_by}")
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        order_clause = f'ORDER BY "{sort_by}" {direction}'
    else:
        # 默认优先按 created_at 或 id 倒序
        if "created_at" in col_names:
            order_clause = 'ORDER BY "created_at" DESC'
        elif "id" in col_names:
            order_clause = 'ORDER BY "id" DESC'

    # 4. 搜索子句 (仅匹配文本列)
    where_clause = ""
    params = {}
    if search and search.strip():
        text_cols = [c["name"] for c in cols if any(t in str(c["type"]).upper() for t in ("CHAR", "TEXT", "STRING"))]
        if text_cols:
            conditions = [f'"{c}" LIKE :search_kw' for c in text_cols]
            where_clause = "WHERE " + " OR ".join(conditions)
            params["search_kw"] = f"%{search.strip()}%"

    # 5. 计算总行数
    count_sql = f'SELECT COUNT(*) FROM "{table_name}" {where_clause}'
    cnt_res = await db.execute(text(count_sql), params)
    total_rows = cnt_res.scalar() or 0
    total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1

    # 6. 分页获取数据
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    data_sql = f'SELECT * FROM "{table_name}" {where_clause} {order_clause} LIMIT :limit OFFSET :offset'
    data_res = await db.execute(text(data_sql), params)
    raw_rows = [dict(r._mapping) for r in data_res.fetchall()]

    # 7. 数据序列化与敏感列脱敏
    cleaned_rows = []
    for r in raw_rows:
        row_dict = {}
        for k, v in r.items():
            # 敏感凭证密码自动安全脱敏
            if "password" in k.lower() or "secret" in k.lower():
                row_dict[k] = "●●●●●● [Argon2id Hash Protected]"
            elif isinstance(v, (datetime, time.struct_time)):
                row_dict[k] = v.isoformat() if hasattr(v, "isoformat") else str(v)
            elif isinstance(v, bytes):
                row_dict[k] = f"<binary {len(v)} bytes>"
            else:
                row_dict[k] = v
        cleaned_rows.append(row_dict)

    meta = TABLE_METADATA_MAP.get(table_name, {"display_name": table_name, "category": "📦 业务数据"})

    return {
        "table_name": table_name,
        "display_name": meta["display_name"],
        "category": meta["category"],
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "columns": [
            {
                "name": c["name"],
                "type": str(c["type"]),
                "nullable": c.get("nullable", True),
                "primary_key": bool(c.get("primary_key", False))
            }
            for c in cols
        ],
        "rows": cleaned_rows
    }


# =========================================================================
# 系统受控附件与多媒体资产管理 (Attachment Management - docs/05 & docs/15)
# =========================================================================

class BindDemoRequest(BaseModel):
    res_model: str
    res_id: str
    demo_filename: str
    description: Optional[str] = None

@router.post("/attachments/upload", response_model=AttachmentResponse, summary="上传受控附件/图片并与业务实体关联")
async def upload_attachment(
    file: UploadFile = File(...),
    res_model: str = Form("system"),
    res_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    通用附件上传：计算 SHA-256 完整性哈希，物理持久化至磁盘，并在 sys_attachments 登记轻量元数据。
    支持自动绑定 hr_employee 的 avatar_url 与 product_master 的 primary_image_url。
    """
    base_uploads = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "uploads"))
    target_dir = os.path.join(base_uploads, res_model)
    os.makedirs(target_dir, exist_ok=True)

    content = await file.read()
    file_size = len(content)
    sha256 = hashlib.sha256(content).hexdigest()

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_name = f"{uuid.uuid4().hex[:12]}{ext}"
    physical_path = os.path.join(target_dir, stored_name)

    with open(physical_path, "wb") as f:
        f.write(content)

    file_url = f"/uploads/{res_model}/{stored_name}"

    attachment = SystemAttachment(
        file_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_path=physical_path,
        file_url=file_url,
        sha256_hash=sha256,
        res_model=res_model,
        res_id=res_id,
        description=description or f"由 {current_user.username} 上传的 {res_model} 附件",
        created_by_id=current_user.id
    )
    db.add(attachment)

    if res_id:
        if res_model == "hr_employee":
            emp = (await db.execute(select(Employee).where(Employee.id == res_id))).scalar_one_or_none()
            if emp:
                emp.avatar_url = file_url
        elif res_model == "product_master":
            prod = (await db.execute(select(ProductMaster).where(ProductMaster.id == res_id))).scalar_one_or_none()
            if prod:
                prod.primary_image_url = file_url

    await db.commit()
    await db.refresh(attachment)
    return attachment

@router.post("/attachments/bind-demo", response_model=AttachmentResponse, summary="一键绑定预置Demo素材至业务实体")
async def bind_demo_attachment(
    payload: BindDemoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    一键将预置 Demo 素材（如 avatar_dr_zhang.svg、product_matrix_led.svg）关联至目标员工或产品
    """
    base_uploads = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "uploads"))
    demo_file_path = os.path.join(base_uploads, "demo", payload.demo_filename)
    
    if not os.path.exists(demo_file_path):
        raise HTTPException(status_code=404, detail=f"预设 Demo 文件 '{payload.demo_filename}' 不存在")

    with open(demo_file_path, "rb") as f:
        content = f.read()

    file_size = len(content)
    sha256 = hashlib.sha256(content).hexdigest()
    file_url = f"/uploads/demo/{payload.demo_filename}"

    attachment = SystemAttachment(
        file_name=payload.demo_filename,
        stored_name=f"demo_{payload.demo_filename}_{uuid.uuid4().hex[:6]}",
        content_type="image/svg+xml" if payload.demo_filename.endswith(".svg") else "image/png",
        file_size=file_size,
        file_path=demo_file_path,
        file_url=file_url,
        sha256_hash=sha256,
        res_model=payload.res_model,
        res_id=payload.res_id,
        description=payload.description or f"关联预置 Demo 素材: {payload.demo_filename}",
        created_by_id=current_user.id
    )
    db.add(attachment)

    if payload.res_id:
        if payload.res_model == "hr_employee":
            emp = (await db.execute(select(Employee).where(Employee.id == payload.res_id))).scalar_one_or_none()
            if emp:
                emp.avatar_url = file_url
        elif payload.res_model == "product_master":
            prod = (await db.execute(select(ProductMaster).where(ProductMaster.id == payload.res_id))).scalar_one_or_none()
            if prod:
                prod.primary_image_url = file_url

    await db.commit()
    await db.refresh(attachment)
    return attachment

@router.get("/attachments", summary="获取全局附件列表")
async def list_attachments(
    res_model: Optional[str] = Query(None, description="按业务模型过滤"),
    res_id: Optional[str] = Query(None, description="按业务实体ID过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(SystemAttachment).where(SystemAttachment.is_deleted == False)
    if res_model:
        stmt = stmt.where(SystemAttachment.res_model == res_model)
    if res_id:
        stmt = stmt.where(SystemAttachment.res_id == res_id)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0

    stmt = stmt.order_by(desc(SystemAttachment.created_at)).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": a.id,
                "file_name": a.file_name,
                "stored_name": a.stored_name,
                "content_type": a.content_type,
                "file_size": a.file_size,
                "file_url": a.file_url,
                "sha256_hash": a.sha256_hash,
                "res_model": a.res_model,
                "res_id": a.res_id,
                "description": a.description,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in items
        ]
    }

@router.get("/attachments/stats", response_model=AttachmentStatsResponse, summary="获取全局附件存储统计指标")
async def get_attachment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(SystemAttachment).where(SystemAttachment.is_deleted == False)
    all_atts = (await db.execute(stmt)).scalars().all()

    total_count = len(all_atts)
    total_size = sum(a.file_size for a in all_atts)
    model_breakdown = {}
    for a in all_atts:
        model_breakdown[a.res_model] = model_breakdown.get(a.res_model, 0) + 1

    return AttachmentStatsResponse(
        total_count=total_count,
        total_size_bytes=total_size,
        total_size_mb=round(total_size / (1024 * 1024), 2),
        model_breakdown=model_breakdown
    )

@router.delete("/attachments/{attachment_id}", summary="删除指定附件与元数据")
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    stmt = select(SystemAttachment).where(SystemAttachment.id == attachment_id, SystemAttachment.is_deleted == False)
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")

    att.is_deleted = True
    await db.commit()
    return {"success": True, "message": f"附件 '{att.file_name}' 已成功安全移除"}

