import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.services import ClusterService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/clusters", tags=["Clusters"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("", response_model=ResponseModel)
def list_clusters(
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data=[])
    
    try:
        cluster_service = ClusterService(vcenter_config, datacenter)
        clusters = cluster_service.list_clusters()
        return ResponseModel(data=clusters)
    except Exception as e:
        logger.error(f"Failed to list clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}", response_model=ResponseModel)
def get_cluster(
    cluster_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        cluster_service = ClusterService(vcenter_config, datacenter)
        cluster = cluster_service.get_cluster(cluster_id)
        
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        return ResponseModel(data=cluster)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}/hosts", response_model=ResponseModel)
def get_cluster_hosts(
    cluster_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        cluster_service = ClusterService(vcenter_config, datacenter)
        hosts = cluster_service.get_cluster_hosts(cluster_id)
        return ResponseModel(data=hosts)
    except Exception as e:
        logger.error(f"Failed to get cluster hosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}/ha", response_model=ResponseModel)
def get_cluster_ha_config(
    cluster_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        cluster_service = ClusterService(vcenter_config, datacenter)
        ha_config = cluster_service.get_ha_config(cluster_id)
        return ResponseModel(data=ha_config)
    except Exception as e:
        logger.error(f"Failed to get HA config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}/drs", response_model=ResponseModel)
def get_cluster_drs_config(
    cluster_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        cluster_service = ClusterService(vcenter_config, datacenter)
        drs_config = cluster_service.get_drs_config(cluster_id)
        return ResponseModel(data=drs_config)
    except Exception as e:
        logger.error(f"Failed to get DRS config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}/resource-pools", response_model=ResponseModel)
def get_cluster_resource_pools(
    cluster_id: str,
    datacenter: Optional[str] = Query(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    from app.services import ResourcePoolService
    
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(status_code=503, detail="vCenter not configured")
    
    try:
        rp_service = ResourcePoolService(vcenter_config, datacenter)
        pools = rp_service.list_resource_pools(cluster_id)
        return ResponseModel(data=pools)
    except Exception as e:
        logger.error(f"Failed to get resource pools: {e}")
        raise HTTPException(status_code=500, detail=str(e))
