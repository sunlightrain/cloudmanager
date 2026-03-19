from typing import Optional, List
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
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


class VMCloneRequest(BaseModel):
    name: str
    target_host_id: Optional[str] = None
    target_datastore_id: Optional[str] = None
    linked_clone: bool = False
    snapshot_id: Optional[str] = None


class VMMigrateRequest(BaseModel):
    target_host_id: Optional[str] = None
    target_datastore_id: Optional[str] = None
    target_cluster_id: Optional[str] = None
    priority: str = "default"


class VMHotResizeRequest(BaseModel):
    cpu: Optional[int] = None
    memory_mb: Optional[int] = None
    disk_gb: Optional[int] = None


@router.post("/{vm_id}/migrate", response_model=ResponseModel)
async def migrate_vm(
    vm_id: str,
    migrate_data: VMMigrateRequest,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.migrate(
        vm_id=vm_id,
        target_host_id=migrate_data.target_host_id,
        target_datastore_id=migrate_data.target_datastore_id,
        target_cluster_id=migrate_data.target_cluster_id,
        priority=migrate_data.priority
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_migrate",
        target=vm_id,
        detail=json.dumps(migrate_data.model_dump())
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/storage-vmotion", response_model=ResponseModel)
async def storage_vmotion(
    vm_id: str,
    target_datastore_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.storage_vmotion(vm_id, target_datastore_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_storage_vmotion",
        target=vm_id,
        detail=f"Target datastore: {target_datastore_id}"
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/hot-resize", response_model=ResponseModel)
async def hot_resize_vm(
    vm_id: str,
    resize_data: VMHotResizeRequest,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.hot_resize(
        vm_id=vm_id,
        cpu=resize_data.cpu,
        memory_mb=resize_data.memory_mb,
        disk_gb=resize_data.disk_gb
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_hot_resize",
        target=vm_id,
        detail=json.dumps(resize_data.model_dump())
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/clone", response_model=ResponseModel)
async def clone_vm(
    vm_id: str,
    clone_data: VMCloneRequest,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.clone(
        vm_id=vm_id,
        name=clone_data.name,
        target_host_id=clone_data.target_host_id,
        target_datastore_id=clone_data.target_datastore_id,
        linked_clone=clone_data.linked_clone,
        snapshot_id=clone_data.snapshot_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_clone",
        target=vm_id,
        detail=f"Cloned to: {clone_data.name}"
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/{vm_id}/convert-to-template", response_model=ResponseModel)
async def convert_to_template(
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.convert_to_template(vm_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_convert_to_template",
        target=vm_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/templates/{template_id}/convert-to-vm", response_model=ResponseModel)
async def convert_to_vm(
    template_id: str,
    target_host_id: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.convert_to_vm(template_id, target_host_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="template_convert_to_vm",
        target=template_id
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message=result["message"], data=result)


@router.post("/batch/power-on", response_model=ResponseModel)
async def batch_power_on(
    vm_ids: List[str],
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.batch_power_on(vm_ids)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_batch_power_on",
        target=",".join(vm_ids)
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message="Batch power on completed", data=result)


@router.post("/batch/power-off", response_model=ResponseModel)
async def batch_power_off(
    vm_ids: List[str],
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.batch_power_off(vm_ids)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_batch_power_off",
        target=",".join(vm_ids)
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message="Batch power off completed", data=result)


@router.post("/batch/delete", response_model=ResponseModel)
async def batch_delete(
    vm_ids: List[str],
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    vm_service = VMService(session)
    result = await vm_service.batch_delete(vm_ids)
    
    log = OperationLog(
        user_id=current_user.id,
        username=current_user.username,
        operation="vm_batch_delete",
        target=",".join(vm_ids)
    )
    session.add(log)
    session.commit()
    
    return ResponseModel(message="Batch delete completed", data=result)
