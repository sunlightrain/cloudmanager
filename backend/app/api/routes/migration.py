import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import MigrationService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/migration", tags=["Migration"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


class VMotionRequest(BaseModel):
    vm_id: str
    target_host_id: Optional[str] = None
    target_cluster_id: Optional[str] = None
    priority: str = "default"


class StorageVMotionRequest(BaseModel):
    vm_id: str
    target_datastore_name: str


@router.post("/vmotion/precheck", response_model=ResponseModel)
def vmotion_precheck(
    request: VMotionRequest,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        migration_service = MigrationService(vcenter_config, datacenter)
        result = migration_service.vmotion_precheck(
            vm_id=request.vm_id,
            target_host_id=request.target_host_id,
            target_cluster_id=request.target_cluster_id
        )
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"vMotion precheck failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vmotion", response_model=ResponseModel)
def execute_vmotion(
    request: VMotionRequest,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    if not request.target_host_id and not request.target_cluster_id:
        raise HTTPException(status_code=400, detail="Must specify target_host_id or target_cluster_id")
    
    try:
        migration_service = MigrationService(vcenter_config, datacenter)
        result = migration_service.execute_vmotion(
            vm_id=request.vm_id,
            target_host_id=request.target_host_id,
            priority=request.priority
        )
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"vMotion execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage-vmotion", response_model=ResponseModel)
def execute_storage_vmotion(
    request: StorageVMotionRequest,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        migration_service = MigrationService(vcenter_config, datacenter)
        result = migration_service.execute_storage_vmotion(
            vm_id=request.vm_id,
            target_datastore_name=request.target_datastore_name
        )
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"Storage vMotion execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
