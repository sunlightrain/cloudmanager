from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.services.monitoring_service import MonitoringService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/alerts", response_model=ResponseModel)
def list_alerts(
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = MonitoringService(session)
    alerts = service.get_alerts(tenant_id, status, severity, limit)
    return ResponseModel(data=[a.model_dump() for a in alerts])


@router.post("/alerts/{alert_id}/acknowledge", response_model=ResponseModel)
def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = MonitoringService(session)
    alert = service.acknowledge_alert(alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return ResponseModel(message="Alert acknowledged")


@router.post("/alerts/{alert_id}/resolve", response_model=ResponseModel)
def resolve_alert(
    alert_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = MonitoringService(session)
    alert = service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return ResponseModel(message="Alert resolved")


@router.get("/alerts/rules", response_model=ResponseModel)
def list_alert_rules(
    resource_type: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = MonitoringService(session)
    rules = service.get_alert_rules(resource_type)
    return ResponseModel(data=[r.model_dump() for r in rules])


@router.post("/alerts/rules", response_model=ResponseModel)
def create_alert_rule(
    name: str,
    resource_type: str,
    metric: str,
    condition: str,
    threshold: float,
    severity: str = "warning",
    duration: int = 0,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = MonitoringService(session)
    rule = service.create_alert_rule(
        name=name,
        resource_type=resource_type,
        metric=metric,
        condition=condition,
        threshold=threshold,
        severity=severity,
        duration=duration
    )
    return ResponseModel(data=rule.model_dump())


@router.get("/metrics/{resource_type}/{resource_id}", response_model=ResponseModel)
def get_metrics(
    resource_type: str,
    resource_id: str,
    metric: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    from datetime import datetime
    
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    service = MonitoringService(session)
    data = service.get_metrics(resource_type, resource_id, metric, start, end, limit)
    
    return ResponseModel(data=[
        {
            "value": dp.value,
            "timestamp": dp.timestamp.isoformat()
        }
        for dp in data
    ])


@router.post("/notifications/channels", response_model=ResponseModel)
def create_notification_channel(
    name: str,
    channel_type: str,
    config: dict,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = MonitoringService(session)
    channel = service.create_notification_channel(name, channel_type, config)
    return ResponseModel(data=channel.model_dump())
