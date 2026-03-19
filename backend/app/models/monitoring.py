from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class AlertRule(SQLModel, table=True):
    __tablename__ = "alert_rules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    resource_type: str
    metric: str
    condition: str
    threshold: float
    duration: int = 0
    severity: str = "warning"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: Optional[int] = Field(foreign_key="alert_rules.id")
    tenant_id: Optional[int] = Field(index=True)
    resource_type: str
    resource_id: str
    metric: str
    value: float
    threshold: float
    severity: str
    status: str = "active"
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolved_at: Optional[datetime] = None


class NotificationChannel(SQLModel, table=True):
    __tablename__ = "notification_channels"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str
    config: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricDataPoint(SQLModel, table=True):
    __tablename__ = "metric_data_points"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_type: str
    resource_id: str
    metric: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
