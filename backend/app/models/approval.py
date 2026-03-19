from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class ApprovalTemplate(SQLModel, table=True):
    __tablename__ = "approval_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    request_type: str
    steps: str
    is_auto_approve: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(SQLModel, table=True):
    __tablename__ = "approval_requests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    request_type: str
    tenant_id: int = Field(index=True)
    applicant_id: int = Field(foreign_key="users.id", index=True)
    resource_type: str
    resource_id: Optional[str] = None
    detail: str
    status: str = "pending"
    template_id: Optional[int] = Field(foreign_key="approval_templates.id")
    current_step: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRecord(SQLModel, table=True):
    __tablename__ = "approval_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="approval_requests.id", index=True)
    step_order: int
    approver_id: int = Field(foreign_key="users.id")
    action: str
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
