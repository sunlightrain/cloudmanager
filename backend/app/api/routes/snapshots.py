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


@router.post("/{vm_id}/cleanup", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def cleanup_snapshots(
    vm_id: str,
    keep_count: int = Query(0, description="Number of latest snapshots to keep"),
    current_user: User = Depends(require_current_user)
):
    client = get_vsphere_client()
    
    try:
        snapshots = client.get_snapshots(vm_id)
        if not snapshots:
            return ResponseModel(message="No snapshots to clean")
        
        snapshots_sorted = sorted(
            snapshots,
            key=lambda x: x.get("created", ""),
            reverse=True
        )
        
        to_delete = snapshots_sorted[keep_count:]
        deleted = []
        failed = []
        
        for snap in to_delete:
            try:
                client.delete_snapshot(vm_id, snap.get("snapshot_id"))
                deleted.append(snap.get("name"))
            except Exception as e:
                failed.append({"name": snap.get("name"), "error": str(e)})
        
        return ResponseModel(
            data={
                "deleted": len(deleted),
                "failed": len(failed),
                "details": {"deleted": deleted, "failed": failed}
            },
            message=f"Cleanup completed: {len(deleted)} deleted, {len(failed)} failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )
