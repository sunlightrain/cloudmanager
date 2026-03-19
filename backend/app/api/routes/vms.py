from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.models.task import Task
from app.models.operation_log import OperationLog
from app.services.vm_service import VMService
from app.schemas.vm import VMCreate, VMUpdate, VMPowerAction, VMResponse, VMListResponse
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])


@router.get("", response_model=ResponseModel)
def list_vms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    client = get_vsphere_client()
    vms = client.get_vms()
    
    if name:
        vms = [vm for vm in vms if name.lower() in vm.get("name", "").lower()]
    if status:
        vms = [vm for vm in vms if vm.get("status") == status]
    
    total = len(vms)
    start = (page - 1) * page_size
    end = start + page_size
    items = vms[start:end]
    
    return ResponseModel(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/{vm_id}", response_model=ResponseModel)
def get_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    client = get_vsphere_client()
    vm = client.get_vm_by_id(vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    return ResponseModel(data=vm)


@router.post("", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def create_vm(
    vm_data: VMCreate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    task = Task(task_type="vm_create", status="pending")
    session.add(task)
    session.commit()
    session.refresh(task)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_create",
        target=vm_data.name,
        detail=vm_data.model_dump_json()
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(
        code=202,
        message="Task created",
        data={
            "task_id": task.task_id,
            "status": task.status
        }
    )


@router.delete("/{vm_id}", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def delete_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    task = Task(task_type="vm_delete", status="pending")
    session.add(task)
    session.commit()
    session.refresh(task)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_delete",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(
        code=202,
        message="Delete task created",
        data={
            "task_id": task.task_id,
            "status": task.status
        }
    )


@router.patch("/{vm_id}", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
def update_vm(
    vm_id: str,
    vm_data: VMUpdate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    task = Task(task_type="vm_update", status="pending")
    session.add(task)
    session.commit()
    session.refresh(task)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_update",
        target=vm_id,
        detail=vm_data.model_dump_json()
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(
        code=202,
        message="Reconfig task created",
        data={
            "task_id": task.task_id,
            "status": task.status
        }
    )


@router.post("/{vm_id}/power", response_model=ResponseModel)
def power_vm(
    vm_id: str,
    action: VMPowerAction,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    client = get_vsphere_client()
    
    if action.action == "start":
        success = client.power_on(vm_id)
    elif action.action == "stop":
        success = client.power_off(vm_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation=f"vm_power_{action.action}",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=f"VM {action.action} successful")


@router.post("/{vm_id}/power-on", response_model=ResponseModel)
async def power_on_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.power_on(vm_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_power_on",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/power-off", response_model=ResponseModel)
async def power_off_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.power_off(vm_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_power_off",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/restart", response_model=ResponseModel)
async def restart_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.restart(vm_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_restart",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/suspend", response_model=ResponseModel)
async def suspend_vm(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.suspend(vm_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_suspend",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.get("/{vm_id}/snapshots", response_model=ResponseModel)
async def list_snapshots(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    snapshots = await vm_service.get_snapshots(vm_id)
    return ResponseModel(data=snapshots)


@router.post("/{vm_id}/snapshots", response_model=ResponseModel)
async def create_snapshot(
    vm_id: str,
    name: str,
    description: str = "",
    memory: bool = False,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.create_snapshot(vm_id, name, description, memory)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_snapshot_create",
        target=vm_id,
        detail=f"Snapshot: {name}"
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/snapshots/{snapshot_id}/revert", response_model=ResponseModel)
async def revert_snapshot(
    vm_id: str,
    snapshot_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.revert_snapshot(vm_id, snapshot_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_snapshot_revert",
        target=vm_id,
        detail=f"Snapshot ID: {snapshot_id}"
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.delete("/{vm_id}/snapshots/{snapshot_id}", response_model=ResponseModel)
async def delete_snapshot(
    vm_id: str,
    snapshot_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.delete_snapshot(vm_id, snapshot_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_snapshot_delete",
        target=vm_id,
        detail=f"Snapshot ID: {snapshot_id}"
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.get("/{vm_id}/performance", response_model=ResponseModel)
def get_vm_performance(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    performance = vm_service.get_vm_performance(vm_id)
    
    if not performance:
        raise HTTPException(status_code=404, detail="VM not found or performance data unavailable")
    
    return ResponseModel(data=performance)
