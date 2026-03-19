import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import DatacenterService, VMService, ClusterService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/hosts", tags=["Hosts"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("", response_model=ResponseModel)
def list_hosts(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        datacenter_service = DatacenterService(vcenter_config, datacenter)
        tree = datacenter_service.get_hierarchy_tree()
        
        all_hosts = []
        for dc in tree.get("datacenters", []):
            for cluster in dc.get("children", []):
                all_hosts.extend(cluster.get("children", []))
        
        return ResponseModel(data=all_hosts)
    except Exception as e:
        logger.error(f"Failed to list hosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", response_model=ResponseModel)
def get_overview(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={})
    
    try:
        datacenter_service = DatacenterService(vcenter_config, datacenter)
        overview = datacenter_service.get_datacenter_overview(datacenter or "Datacenter")
        return ResponseModel(data=overview)
    except Exception as e:
        logger.error(f"Failed to get overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{host_id}", response_model=ResponseModel)
def get_host(
    host_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        datacenter_service = DatacenterService(vcenter_config, datacenter)
        tree = datacenter_service.get_hierarchy_tree()
        
        for dc in tree.get("datacenters", []):
            for cluster in dc.get("children", []):
                for host in cluster.get("children", []):
                    if host.get("id") == host_id:
                        return ResponseModel(data=host)
        
        raise HTTPException(status_code=404, detail="Host not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get host: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{host_id}/vms", response_model=ResponseModel)
def get_host_vms(
    host_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        vm_service = VMService(vcenter_config, datacenter)
        all_vms = vm_service.list_vms()
        
        host_vms = [vm for vm in all_vms if vm.get("host_id") == host_id]
        
        return ResponseModel(data=host_vms)
    except Exception as e:
        logger.error(f"Failed to get host VMs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
