import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import NetworkService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/networks", tags=["Networks"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("", response_model=ResponseModel)
def list_networks(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        network_service = NetworkService(vcenter_config, datacenter)
        networks = network_service.list_networks()
        return ResponseModel(data=networks)
    except Exception as e:
        logger.error(f"Failed to list networks: {e}")
        return ResponseModel(data=[])


@router.get("/overview", response_model=ResponseModel)
def get_network_overview(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={})
    
    try:
        network_service = NetworkService(vcenter_config, datacenter)
        overview = network_service.get_network_overview()
        return ResponseModel(data=overview)
    except Exception as e:
        logger.error(f"Failed to get network overview: {e}")
        return ResponseModel(data={})


@router.get("/standard-switches", response_model=ResponseModel)
def list_standard_switches(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        network_service = NetworkService(vcenter_config, datacenter)
        switches = network_service.list_standard_switches()
        return ResponseModel(data=switches)
    except Exception as e:
        logger.error(f"Failed to list standard switches: {e}")
        return ResponseModel(data=[])


@router.get("/distributed-switches", response_model=ResponseModel)
def list_distributed_switches(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        network_service = NetworkService(vcenter_config, datacenter)
        switches = network_service.list_distributed_switches()
        return ResponseModel(data=switches)
    except Exception as e:
        logger.error(f"Failed to list distributed switches: {e}")
        return ResponseModel(data=[])


@router.get("/port-groups", response_model=ResponseModel)
def list_port_groups(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        network_service = NetworkService(vcenter_config, datacenter)
        port_groups = network_service.list_port_groups()
        return ResponseModel(data=port_groups)
    except Exception as e:
        logger.error(f"Failed to list port groups: {e}")
        return ResponseModel(data=[])
