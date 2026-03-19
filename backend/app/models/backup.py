from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class BackupPolicy(SQLModel, table=True):
    __tablename__ = "backup_policies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    tenant_id: int = Field(index=True)
    target_type: str
    target_ids: Optional[str] = None
    backup_type: str = "full"
    schedule: str
    retention_count: int = 7
    is_active: bool = True
    last_backup_at: Optional[datetime] = None
    next_backup_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BackupJob(SQLModel, table=True):
    __tablename__ = "backup_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    policy_id: Optional[int] = Field(foreign_key="backup_policies.id")
    resource_type: str
    resource_id: str
    backup_type: str
    status: str = "pending"
    size_bytes: Optional[int] = None
    backup_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BackupFile(SQLModel, table=True):
    __tablename__ = "backup_files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    backup_job_id: int = Field(foreign_key="backup_jobs.id")
    file_path: str
    file_size: int
    file_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
