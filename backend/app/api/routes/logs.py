from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.models.operation_log import OperationLog
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/logs", tags=["Operation Logs"])


@router.get("", response_model=ResponseModel)
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    operation: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    query = session.query(OperationLog)
    
    if operation:
        query = query.filter(OperationLog.operation == operation)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    
    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    items = [{
        "id": log.id,
        "username": log.username,
        "operation": log.operation,
        "target": log.target,
        "detail": log.detail,
        "created_at": log.created_at
    } for log in logs]
    
    return ResponseModel(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )
