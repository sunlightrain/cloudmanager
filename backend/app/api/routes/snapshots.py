from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/snapshots", tags=["Snapshots"])


@router.get("/{vm_id}", response_model=ResponseModel)
def list_snapshots(
    vm_id: str,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    snapshots = client.get_snapshots(vm_id)
    
    return ResponseModel(data=snapshots)


@router.post("/{vm_id}", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def create_snapshot(
    vm_id: str,
    name: str = Query(...),
    description: str = "",
    memory: bool = False,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    success = client.create_snapshot(vm_id, name, description, memory)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create snapshot"
        )
    
    return ResponseModel(message="Snapshot created successfully")


@router.post("/{vm_id}/{snapshot_id}/revert", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def revert_snapshot(
    vm_id: str,
    snapshot_id: str,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    success = client.revert_snapshot(vm_id, snapshot_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revert snapshot"
        )
    
    return ResponseModel(message="Snapshot reverted successfully")


@router.delete("/{vm_id}/{snapshot_id}", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def delete_snapshot(
    vm_id: str,
    snapshot_id: str,
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    success = client.delete_snapshot(vm_id, snapshot_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete snapshot"
        )
    
    return ResponseModel(message="Snapshot deleted successfully")
