from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    task_type: str = Field()
    status: str = Field(default="pending")
    result: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    async def update_status(self, status: str, result: Optional[str] = None, error: Optional[str] = None):
        self.status = status
        if result:
            self.result = result
        if error:
            self.error = error
        if status in ["completed", "failed"]:
            self.completed_at = datetime.utcnow()
