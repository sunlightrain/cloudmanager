from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/clone", tags=["VM Clone"])


class CloneRequest(BaseModel):
    vm_id: str
    name: str
    resource_pool: Optional[str] = None


@router.post("", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def clone_vm(
    request: CloneRequest,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    result = client.clone_vm(request.vm_id, request.name, request.resource_pool)
    
    return ResponseModel(
        code=202,
        message="VM clone started",
        data=result
    )
