from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)
    parent_id: Optional[int] = Field(default=None, index=True)
    level: int = 0
    quota_cpu: int = 100
    quota_memory_gb: int = 512
    quota_storage_gb: int = 1000
    quota_vm_count: int = 50
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def path(self) -> List[str]:
        return []


class TenantUser(SQLModel, table=True):
    __tablename__ = "tenant_users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role: str = "member"
    created_at: datetime = Field(default_factory=datetime.utcnow)
