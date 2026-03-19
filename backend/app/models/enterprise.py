from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None)
    level: int = Field(default=1)
    description: Optional[str] = Field(default=None)
    quota: dict = Field(default={
        "cpu_cores": 100,
        "memory_gb": 512,
        "storage_tb": 10,
        "vm_count": 50
    }, sa_type=JSON)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationUser(SQLModel, table=True):
    __tablename__ = "organization_users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organizations.id")
    user_id: int = Field(foreign_key="users.id")
    role: str = Field(default="member")
    is_default_org: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TenantVM(SQLModel, table=True):
    __tablename__ = "tenant_vms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    vm_id: str = Field(index=True)
    name: str = Field()
    cpu: int = Field(default=0)
    memory_mb: int = Field(default=0)
    disk_gb: int = Field(default=0)
    status: str = Field(default="unknown")
    ip_address: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Request(SQLModel, table=True):
    __tablename__ = "requests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    user_id: int = Field(foreign_key="users.id")
    type: str = Field(index=True)
    status: str = Field(default="pending", index=True)
    title: str = Field()
    details: dict = Field(default={}, sa_type=JSON)
    approval_chain: list = Field(default=[], sa_type=JSON)
    current_approval_level: int = Field(default=0)
    result: Optional[str] = Field(default=None)
    executed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalAction(SQLModel, table=True):
    __tablename__ = "approval_actions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="requests.id")
    approver_id: int = Field(foreign_key="users.id")
    level: int = Field(default=1)
    action: str = Field()
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduledTask(SQLModel, table=True):
    __tablename__ = "scheduled_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    vm_id: Optional[int] = Field(default=None, foreign_key="tenant_vms.id")
    task_type: str = Field(index=True)
    cron_expression: str = Field()
    task_params: dict = Field(default={}, sa_type=JSON)
    enabled: bool = Field(default=True)
    last_run_at: Optional[datetime] = Field(default=None)
    next_run_at: Optional[datetime] = Field(default=None)
    run_count: int = Field(default=0)
    success_count: int = Field(default=0)
    fail_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduledTaskLog(SQLModel, table=True):
    __tablename__ = "scheduled_task_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="scheduled_tasks.id")
    status: str = Field()
    result: Optional[str] = Field(default=None)
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    rule_id: Optional[int] = Field(default=None)
    entity_type: str = Field(index=True)
    entity_id: str = Field(index=True)
    severity: str = Field(default="warning")
    metric_name: Optional[str] = Field(default=None)
    metric_value: Optional[float] = Field(default=None)
    message: str = Field()
    status: str = Field(default="firing", index=True)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)
    notified_at: Optional[datetime] = Field(default=None)


class AlertRule(SQLModel, table=True):
    __tablename__ = "alert_rules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    name: str = Field()
    description: Optional[str] = Field(default=None)
    entity_type: str = Field()
    metric_name: str = Field()
    condition: str = Field()
    threshold: float = Field()
    duration_minutes: int = Field(default=5)
    severity: str = Field(default="warning")
    enabled: bool = Field(default=True)
    notification_channels: list = Field(default=["站内信"], sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BackupJob(SQLModel, table=True):
    __tablename__ = "backup_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    vm_id: Optional[int] = Field(default=None, foreign_key="tenant_vms.id")
    backup_type: str = Field(default="full")
    status: str = Field(default="pending", index=True)
    backup_size_gb: Optional[float] = Field(default=None)
    retention_days: int = Field(default=7)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BackupPolicy(SQLModel, table=True):
    __tablename__ = "backup_policies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    name: str = Field()
    description: Optional[str] = Field(default=None)
    backup_type: str = Field(default="full")
    schedule: str = Field()
    retention_days: int = Field(default=7)
    enabled: bool = Field(default=True)
    target_vm_ids: list = Field(default=[], sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceCatalog(SQLModel, table=True):
    __tablename__ = "service_catalog"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(unique=True, index=True)
    organization_id: int = Field(foreign_key="organizations.id")
    name: str = Field()
    category: str = Field(default="standard")
    description: Optional[str] = Field(default=None)
    specs: dict = Field(default={
        "cpu": 2,
        "memory_gb": 4,
        "disk_gb": 40,
        "template": "ubuntu22"
    }, sa_type=JSON)
    is_public: bool = Field(default=True)
    usage_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MetricSample(SQLModel, table=True):
    __tablename__ = "metric_samples"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True)
    entity_id: str = Field(index=True)
    metric_name: str = Field(index=True)
    value: float = Field()
    unit: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
