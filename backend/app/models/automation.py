from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ScheduledTask(SQLModel, table=True):
    __tablename__ = "scheduled_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    task_type: str
    target_type: str
    target_ids: Optional[str] = None
    cron_expression: str
    action_params: Optional[str] = None
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceTemplate(SQLModel, table=True):
    __tablename__ = "service_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: str
    cpu: int
    memory_mb: int
    disk_gb: int
    os_type: str
    price: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VMInitConfig(SQLModel, table=True):
    __tablename__ = "vm_init_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vm_id: Optional[int] = Field(default=None, index=True)
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    gateway: Optional[str] = None
    dns_servers: Optional[str] = None
    dns_suffix: Optional[str] = None
    custom_script: Optional[str] = None
    password: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
