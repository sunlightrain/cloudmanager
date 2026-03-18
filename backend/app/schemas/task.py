from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20
