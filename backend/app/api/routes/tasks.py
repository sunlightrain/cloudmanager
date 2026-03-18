from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskResponse, TaskListResponse
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=ResponseModel)
def get_task(
    task_id: str,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    task = session.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        return ResponseModel(code=404, message="Task not found")
    
    return ResponseModel(data={
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    })


@router.get("", response_model=ResponseModel)
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    query = session.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    total = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    items = [{
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    } for task in tasks]
    
    return ResponseModel(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )
