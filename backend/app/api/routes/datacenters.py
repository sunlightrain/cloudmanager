import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import DatacenterService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/datacenters", tags=["Datacenters"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("", response_model=ResponseModel)
def list_datacenters(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        datacenter_service = DatacenterService(vcenter_config)
        tree = datacenter_service.get_hierarchy_tree()
        return ResponseModel(data=tree)
    except Exception as e:
        logger.error(f"Failed to list datacenters: {e}")
        return ResponseModel(data={"datacenters": [], "total_datacenters": 0})


@router.get("/tree", response_model=ResponseModel)
def get_datacenter_tree(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={"datacenters": []})
    
    try:
        datacenter_service = DatacenterService(vcenter_config)
        tree = datacenter_service.get_hierarchy_tree()
        return ResponseModel(data=tree)
    except Exception as e:
        logger.error(f"Failed to get datacenter tree: {e}")
        return ResponseModel(data={"datacenters": []})


@router.get("/{datacenter_name}/overview", response_model=ResponseModel)
def get_datacenter_overview(
    datacenter_name: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={})
    
    try:
        datacenter_service = DatacenterService(vcenter_config)
        overview = datacenter_service.get_datacenter_overview(datacenter_name)
        return ResponseModel(data=overview)
    except Exception as e:
        logger.error(f"Failed to get datacenter overview: {e}")
        return ResponseModel(data={})
