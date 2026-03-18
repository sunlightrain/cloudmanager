from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class OperationLog(SQLModel, table=True):
    __tablename__ = "operation_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None)
    operation: str = Field(index=True)
    target: str = Field()
    detail: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
