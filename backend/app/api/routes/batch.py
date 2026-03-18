from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/batch", tags=["Batch Operations"])


class BatchPowerRequest(BaseModel):
    vm_ids: List[str]
    action: str


class BatchDeleteRequest(BaseModel):
    vm_ids: List[str]


@router.post("/power", response_model=ResponseModel)
def batch_power_operation(
    request: BatchPowerRequest,
    current_user: User = Depends(require_current_user)
):
    if request.action not in ["start", "stop", "restart"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be start, stop, or restart"
        )
    
    client = get_vsphere_client()
    results = []
    
    for vm_id in request.vm_ids:
        try:
            if request.action == "start":
                success = client.power_on(vm_id)
            elif request.action == "stop":
                success = client.power_off(vm_id)
            else:
                success = client.restart_vm(vm_id)
            
            results.append({"vm_id": vm_id, "success": success})
        except Exception as e:
            results.append({"vm_id": vm_id, "success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r.get("success"))
    
    return ResponseModel(
        message=f"Batch {request.action} completed: {success_count}/{len(request.vm_ids)} successful",
        data=results
    )


@router.post("/delete", response_model=ResponseModel)
def batch_delete(
    request: BatchDeleteRequest,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    results = []
    
    for vm_id in request.vm_ids:
        try:
            success = client.delete_vm(vm_id)
            results.append({"vm_id": vm_id, "success": success})
        except Exception as e:
            results.append({"vm_id": vm_id, "success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r.get("success"))
    
    return ResponseModel(
        message=f"Batch delete completed: {success_count}/{len(request.vm_ids)} successful",
        data=results
    )
