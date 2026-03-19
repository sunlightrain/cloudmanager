import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.models.task import Task
from app.models.operation_log import OperationLog
from app.schemas.vm import VMCreate, VMUpdate, VMPowerAction, VMResponse, VMListResponse
from app.schemas.common import ResponseModel
from app.core.vsphere import get_vsphere_client

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])


@router.get("", response_model=ResponseModel)
@limiter.limit("100/minute")
def list_vms(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} listing VMs")
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
@limiter.limit("60/minute")
def get_vm(
    request: Request,
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} getting VM {vm_id}")
    client = get_vsphere_client()
    vm = client.get_vm_by_id(vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    return ResponseModel(data=vm)


@router.post("", response_model=ResponseModel, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("30/minute")
def create_vm(
    request: Request,
    vm_data: VMCreate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} creating VM: {vm_data.name}")
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
@limiter.limit("20/minute")
def delete_vm(
    request: Request,
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} deleting VM: {vm_id}")
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
@limiter.limit("30/minute")
def update_vm(
    request: Request,
    vm_id: str,
    vm_data: VMUpdate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} updating VM: {vm_id}")
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
@limiter.limit("60/minute")
def power_vm(
    request: Request,
    vm_id: str,
    action: VMPowerAction,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} power action {action.action} on VM {vm_id}")
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
