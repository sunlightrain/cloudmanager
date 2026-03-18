from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/hosts", tags=["Hosts"])


@router.get("", response_model=ResponseModel)
def list_hosts(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    client = get_vsphere_client()
    hosts = client.get_hosts()
    
    return ResponseModel(data=hosts)


@router.get("/overview", response_model=ResponseModel)
def get_overview(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    client = get_vsphere_client()
    hosts = client.get_hosts()
    vms = client.get_vms()
    
    powered_on = sum(1 for vm in vms if vm.get("status") == "poweredOn")
    powered_off = sum(1 for vm in vms if vm.get("status") == "poweredOff")
    
    return ResponseModel(data={
        "total_hosts": len(hosts),
        "total_vms": len(vms),
        "vm_by_status": {
            "poweredOn": powered_on,
            "poweredOff": powered_off
        }
    })
