from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.vsphere import get_vsphere_client, VSphereConnectionError
from app.services.inventory_service import InventoryService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/sync", response_model=ResponseModel)
def sync_inventory(session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        result = inventory_service.sync_all()
        return ResponseModel(data=result, message="Sync completed")
    except VSphereConnectionError as e:
        raise HTTPException(status_code=503, detail=f"vCenter connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/datacenters", response_model=ResponseModel)
def list_datacenters(datacenter_id: Optional[int] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        if datacenter_id:
            datacenters = [inventory_service.get_datacenters()[0]] if inventory_service.get_datacenters() else []
        else:
            datacenters = inventory_service.get_datacenters()
        return ResponseModel(data=[dc.model_dump() for dc in datacenters])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters", response_model=ResponseModel)
def list_clusters(datacenter_id: Optional[int] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        clusters = inventory_service.get_clusters(datacenter_id)
        return ResponseModel(data=[c.model_dump() for c in clusters])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hosts", response_model=ResponseModel)
def list_hosts(cluster_id: Optional[int] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        hosts = inventory_service.get_hosts(cluster_id)
        return ResponseModel(data=[h.model_dump() for h in hosts])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vms", response_model=ResponseModel)
def list_vms(host_id: Optional[int] = None, status: Optional[str] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        vms = inventory_service.get_vms(host_id, status)
        return ResponseModel(data=[vm.to_summary() for vm in vms])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datastores", response_model=ResponseModel)
def list_datastores(datacenter_id: Optional[int] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        datastores = inventory_service.get_datastores(datacenter_id)
        return ResponseModel(data=[ds.model_dump() for ds in datastores])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/networks", response_model=ResponseModel)
def list_networks(datacenter_id: Optional[int] = None, session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        networks = inventory_service.get_networks(datacenter_id)
        return ResponseModel(data=[n.model_dump() for n in networks])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", response_model=ResponseModel)
def get_overview(session: Session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session)
        overview = inventory_service.get_overview()
        return ResponseModel(data=overview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
