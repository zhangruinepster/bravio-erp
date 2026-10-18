from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_superuser
from app.models.user import User
from .schemas import BackupRecordResponse, CreateBackupRequest
from .service import BackupService

router = APIRouter(prefix="/system/backups", tags=["系统数据库一致性与安全备份 (docs/05)"])

@router.get("", response_model=List[BackupRecordResponse], summary="查询数据库快照历史与防篡改校验码 (限系统管理员)")
async def list_backups(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_superuser)
):
    return await BackupService.list_backups(db)

@router.post("/snapshot", response_model=BackupRecordResponse, status_code=status.HTTP_201_CREATED, summary="手动创建数据库一致性事务快照 (限系统管理员)")
async def create_snapshot(
    req: CreateBackupRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_superuser)
):
    notes = req.notes or f"管理员 [{current_admin.username}] 触发快照"
    return await BackupService.trigger_snapshot(db, notes, current_admin.id)

@router.get("/{backup_id}/verify", summary="防篡改 SHA256 一致性校验与回滚安全评估 (限系统管理员)")
async def verify_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_superuser)
):
    return await BackupService.verify_integrity(db, backup_id)
