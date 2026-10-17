from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.logger import logger
from app.core.config import settings
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse, UserBrief
from app.schemas.user import UserRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证与安全"])

@router.post("/login", response_model=LoginResponse, summary="企业用户登录")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    企业门户统一登录入口：
    - 支持用户名或工作邮箱登录
    - 记录安全审计流水与 IP
    - 返回高安全性 JWT Access Token
    """
    request_id = getattr(request.state, "request_id", "N/A")
    client_ip = request.client.host if request.client else "unknown"

    # 查询用户（支持用户名或邮箱）
    stmt = select(User).where(
        or_(User.username == payload.username, User.email == payload.username),
        User.is_deleted == False
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"[{request_id}] 登录失败: 用户名或密码错误 (Input: {payload.username}, IP: {client_ip})")
        # 写入失败审计日志
        audit = AuditLog(
            request_id=request_id,
            username=payload.username,
            action="AUTH_LOGIN_FAILED",
            module="auth",
            client_ip=client_ip,
            status="FAILED",
            details="用户名或密码校验不匹配"
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误，请核对后重试"
        )

    if not user.is_active:
        logger.warning(f"[{request_id}] 登录被拒: 用户已被停用 (User: {user.username})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前账号已被停用，请联系企业 IT 管理员"
        )

    # 更新最后登录时间与 IP
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_ip

    # 写入成功审计日志
    audit = AuditLog(
        request_id=request_id,
        user_id=user.id,
        username=user.username,
        action="AUTH_LOGIN_SUCCESS",
        module="auth",
        client_ip=client_ip,
        status="SUCCESS",
        details=f"用户成功登录，角色: {user.role}"
    )
    db.add(audit)
    await db.commit()

    # 签发 JWT
    access_token = create_access_token(
        subject=user.id,
        extra_claims={
            "username": user.username,
            "role": user.role,
            "is_superuser": user.is_superuser
        }
    )

    logger.info(f"[{request_id}] ✅ 用户 [{user.username}] 登录成功 (角色: {user.role}, IP: {client_ip})")

    return LoginResponse(
        success=True,
        message="登录成功，欢迎访问 Bravio ERP",
        token=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        user=UserBrief(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_superuser=user.is_superuser
        )
    )

@router.post("/login-form", response_model=TokenResponse, summary="Swagger UI 兼容登录")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    提供给 OpenAPI / Swagger 文档界面的登录测试端点
    """
    stmt = select(User).where(
        or_(User.username == form_data.username, User.email == form_data.username),
        User.is_deleted == False
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"username": user.username, "role": user.role}
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserRead, summary="获取当前登录用户详情")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前通过验证的会话用户信息
    """
    return current_user

@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    登出并记录安全审计
    """
    request_id = getattr(request.state, "request_id", "N/A")
    client_ip = request.client.host if request.client else "unknown"

    audit = AuditLog(
        request_id=request_id,
        user_id=current_user.id,
        username=current_user.username,
        action="AUTH_LOGOUT",
        module="auth",
        client_ip=client_ip,
        status="SUCCESS",
        details="用户主动登出"
    )
    db.add(audit)
    await db.commit()

    logger.info(f"[{request_id}] 用户 [{current_user.username}] 已成功登出")
    return {"success": True, "message": "已安全退出登录"}
