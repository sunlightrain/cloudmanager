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
from app.core.vsphere.client import get_vsphere_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])


def get_vcenter_config():
    return {
        "host": settings.vsphere_host or "localhost",
        "port": settings.vsphere_port or 443,
        "username": settings.vsphere_username or "",
        "password": settings.vsphere_password or "",
    }


@router.get("", response_model=ResponseModel)
@limiter.limit("100/minute")
def list_vms(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} listing VMs")
    
    vcenter_config = get_vcenter_config()
    if not vcenter_config["host"] or not vcenter_config["username"]:
        return ResponseModel(data={"items": [], "total": 0, "page": page, "page_size": page_size})
    
    try:
        with get_vsphere_client(**vcenter_config) as client:
            vms = client.get_all_vms()
            
            vm_list = []
            for vm in vms:
                try:
                    vm_data = client._format_vm(vm)
                    vm_list.append(vm_data)
                except:
                    pass
            
            if name:
                vm_list = [vm for vm in vm_list if name.lower() in vm.get("name", "").lower()]
            if status_filter:
                vm_list = [vm for vm in vm_list if vm.get("status") == status_filter]
            
            total = len(vm_list)
            start = (page - 1) * page_size
            end = start + page_size
            items = vm_list[start:end]
            
            return ResponseModel(
                data={
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            )
    except Exception as e:
        logger.error(f"Failed to list VMs: {e}")
        return ResponseModel(data={"items": [], "total": 0, "page": page, "page_size": page_size})


@router.get("/{vm_id}", response_model=ResponseModel)
@limiter.limit("60/minute")
def get_vm(
    request: Request,
    vm_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User {current_user.username} getting VM {vm_id}")
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vCenter not configured"
        )
    
    try:
        with get_vsphere_client(**vcenter_config) as client:
            vm = client.get_vm_by_id(vm_id)
            
            if not vm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="VM not found"
                )
            
            return ResponseModel(data=vm)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
    vcenter_config = get_vcenter_config()
    
    if not vcenter_config["host"] or not vcenter_config["username"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vCenter not configured"
        )
    
    try:
        with get_vsphere_client(**vcenter_config) as client:
            vms = client.get_all_vms()
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="VM not found"
                )
            
            if action.action == "start":
                client.power_on_vm(vm)
            elif action.action == "stop":
                client.power_off_vm(vm)
            elif action.action == "restart":
                client.power_off_vm(vm)
                client.power_on_vm(vm)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid action"
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Power operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
