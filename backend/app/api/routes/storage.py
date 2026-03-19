import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/storage", tags=["Storage"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("/datastores", response_model=ResponseModel)
def list_datastores(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        storage_service = StorageService(vcenter_config, datacenter)
        datastores = storage_service.list_datastores()
        return ResponseModel(data=datastores)
    except Exception as e:
        logger.error(f"Failed to list datastores: {e}")
        return ResponseModel(data=[])


@router.get("/datastores/overview", response_model=ResponseModel)
def get_storage_overview(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={})
    
    try:
        storage_service = StorageService(vcenter_config, datacenter)
        overview = storage_service.get_storage_overview()
        return ResponseModel(data=overview)
    except Exception as e:
        logger.error(f"Failed to get storage overview: {e}")
        return ResponseModel(data={})


@router.get("/datastores/{datastore_id}", response_model=ResponseModel)
def get_datastore(
    datastore_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        storage_service = StorageService(vcenter_config, datacenter)
        datastore = storage_service.get_datastore(datastore_id)
        
        if not datastore:
            raise HTTPException(status_code=404, detail="Datastore not found")
        
        return ResponseModel(data=datastore)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get datastore: {e}")
        raise HTTPException(status_code=500, detail=str(e))
