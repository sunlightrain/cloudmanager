from fastapi import APIRouter, Depends
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure"])


@router.get("/datastores", response_model=ResponseModel)
def list_datastores(current_user: User = Depends(require_current_user)):
    client = get_vsphere_client()
    datastores = client.get_datastores()
    
    return ResponseModel(data=datastores)


@router.get("/networks", response_model=ResponseModel)
def list_networks(current_user: User = Depends(require_current_user)):
    client = get_vsphere_client()
    networks = client.get_networks()
    
    return ResponseModel(data=networks)


@router.get("/clusters", response_model=ResponseModel)
def list_clusters(current_user: User = Depends(require_current_user)):
    client = get_vsphere_client()
    clusters = client.get_clusters()
    
    return ResponseModel(data=clusters)


@router.get("/datacenters", response_model=ResponseModel)
def list_datacenters(current_user: User = Depends(require_current_user)):
    client = get_vsphere_client()
    datacenters = client.get_datacenters()
    
    return ResponseModel(data=datacenters)


@router.get("/hosts/{host_id}", response_model=ResponseModel)
def get_host_detail(host_id: str, current_user: User = Depends(require_current_user)):
    client = get_vsphere_client()
    host = client.get_host_by_id(host_id)
    
    if not host:
        return ResponseModel(code=404, message="Host not found")
    
    return ResponseModel(data=host)
