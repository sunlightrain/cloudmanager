from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.services.backup_service import BackupService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/backups", tags=["Backups"])


@router.get("/policies", response_model=ResponseModel)
def list_backup_policies(
    tenant_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = BackupService(session)
    policies = service.get_backup_policies(tenant_id)
    return ResponseModel(data=[p.model_dump() for p in policies])


@router.post("/policies", response_model=ResponseModel)
def create_backup_policy(
    name: str,
    tenant_id: int,
    target_type: str,
    target_ids: Optional[List[str]] = None,
    backup_type: str = "full",
    schedule: str = "daily",
    retention_count: int = 7,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = BackupService(session)
    policy = service.create_backup_policy(
        name=name,
        tenant_id=tenant_id,
        target_type=target_type,
        target_ids=target_ids,
        backup_type=backup_type,
        schedule=schedule,
        retention_count=retention_count
    )
    return ResponseModel(data=policy.model_dump())


@router.get("/jobs", response_model=ResponseModel)
def list_backup_jobs(
    policy_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = BackupService(session)
    jobs = service.get_backup_jobs(policy_id, resource_type, status, limit)
    return ResponseModel(data=[j.model_dump() for j in jobs])


@router.post("/jobs", response_model=ResponseModel)
def create_backup_job(
    resource_type: str,
    resource_id: str,
    backup_type: str = "full",
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = BackupService(session)
    job = service.create_backup_job(
        resource_type=resource_type,
        resource_id=resource_id,
        backup_type=backup_type
    )
    return ResponseModel(data=job.model_dump())


@router.post("/jobs/{job_id}/restore", response_model=ResponseModel)
def restore_backup(
    job_id: int,
    restore_type: str = "original",
    target_host_id: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = BackupService(session)
    result = service.restore_backup(job_id, restore_type, target_host_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Restore failed"))
    return ResponseModel(message="Restore initiated", data=result)


@router.get("/history/{resource_type}/{resource_id}", response_model=ResponseModel)
def get_backup_history(
    resource_type: str,
    resource_id: str,
    limit: int = 50,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = BackupService(session)
    history = service.get_backup_history(resource_type, resource_id, limit)
    return ResponseModel(data=history)
