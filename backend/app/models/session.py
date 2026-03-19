from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlmodel import SQLModel, Field


class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
