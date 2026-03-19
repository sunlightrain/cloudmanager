from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.services.automation_service import AutomationService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/automation", tags=["Automation"])


@router.get("/scheduled-tasks", response_model=ResponseModel)
def list_scheduled_tasks(
    task_type: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = AutomationService(session)
    tasks = service.get_scheduled_tasks(task_type)
    return ResponseModel(data=[t.model_dump() for t in tasks])


@router.post("/scheduled-tasks", response_model=ResponseModel)
def create_scheduled_task(
    name: str,
    task_type: str,
    target_type: str,
    cron_expression: str,
    target_ids: Optional[List[str]] = None,
    action_params: Optional[dict] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = AutomationService(session)
    task = service.create_scheduled_task(
        name=name,
        task_type=task_type,
        target_type=target_type,
        cron_expression=cron_expression,
        target_ids=target_ids,
        action_params=action_params
    )
    return ResponseModel(data=task.model_dump())


@router.post("/scheduled-tasks/{task_id}/run", response_model=ResponseModel)
def run_scheduled_task(
    task_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = AutomationService(session)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = service.execute_task(task)
    return ResponseModel(data=result)


@router.get("/service-templates", response_model=ResponseModel)
def list_service_templates(
    category: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = AutomationService(session)
    templates = service.get_service_templates(category)
    return ResponseModel(data=[t.model_dump() for t in templates])


@router.post("/service-templates", response_model=ResponseModel)
def create_service_template(
    name: str,
    category: str,
    cpu: int,
    memory_mb: int,
    disk_gb: int,
    os_type: str,
    price: Optional[float] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = AutomationService(session)
    template = service.create_service_template(
        name=name,
        category=category,
        cpu=cpu,
        memory_mb=memory_mb,
        disk_gb=disk_gb,
        os_type=os_type,
        price=price
    )
    return ResponseModel(data=template.model_dump())
