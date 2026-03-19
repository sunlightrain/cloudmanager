import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from croniter import croniter

from app.models.enterprise import (
    ScheduledTask, ScheduledTaskLog, Alert, AlertRule, 
    MetricSample, BackupJob, BackupPolicy, ServiceCatalog
)

logger = logging.getLogger(__name__)


class ScheduledTaskService:
    def __init__(self, session: Session):
        self.session = session

    def create_task(
        self,
        organization_id: int,
        task_type: str,
        cron_expression: str,
        vm_id: Optional[int] = None,
        task_params: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ) -> ScheduledTask:
        task = ScheduledTask(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            vm_id=vm_id,
            task_type=task_type,
            cron_expression=cron_expression,
            task_params=task_params or {},
            enabled=enabled
        )
        
        try:
            cron = croniter(cron_expression, datetime.now())
            task.next_run_at = cron.get_next(datetime)
        except:
            task.next_run_at = datetime.now() + timedelta(hours=1)
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        return self.session.get(ScheduledTask, task_id)

    def list_tasks(self, organization_id: Optional[int] = None, enabled: Optional[bool] = None) -> List[ScheduledTask]:
        query = self.session.query(ScheduledTask)
        if organization_id:
            query = query.filter(ScheduledTask.organization_id == organization_id)
        if enabled is not None:
            query = query.filter(ScheduledTask.enabled == enabled)
        return query.order_by(ScheduledTask.created_at.desc()).all()

    def update_task(
        self,
        task_id: int,
        cron_expression: Optional[str] = None,
        task_params: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None
    ) -> Optional[ScheduledTask]:
        task = self.session.get(ScheduledTask, task_id)
        if not task:
            return None
        
        if cron_expression is not None:
            task.cron_expression = cron_expression
            try:
                cron = croniter(cron_expression, datetime.now())
                task.next_run_at = cron.get_next(datetime)
            except:
                pass
        
        if task_params is not None:
            task.task_params = task_params
        if enabled is not None:
            task.enabled = enabled
        
        task.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self.session.get(ScheduledTask, task_id)
        if not task:
            return False
        self.session.delete(task)
        self.session.commit()
        return True

    def log_execution(
        self,
        task_id: int,
        status: str,
        result: Optional[str] = None
    ):
        task = self.session.get(ScheduledTask, task_id)
        if not task:
            return
        
        log = ScheduledTaskLog(
            task_id=task_id,
            status=status,
            result=result,
            executed_at=datetime.utcnow()
        )
        self.session.add(log)
        
        task.last_run_at = datetime.utcnow()
        task.run_count += 1
        if status == "success":
            task.success_count += 1
        else:
            task.fail_count += 1
        
        try:
            cron = croniter(task.cron_expression, datetime.now())
            task.next_run_at = cron.get_next(datetime)
        except:
            pass
        
        self.session.commit()

    def get_due_tasks(self) -> List[ScheduledTask]:
        now = datetime.now()
        return self.session.query(ScheduledTask).filter(
            ScheduledTask.enabled == True,
            ScheduledTask.next_run_at <= now
        ).all()


class AlertService:
    def __init__(self, session: Session):
        self.session = session

    def create_alert(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: str,
        severity: str,
        message: str,
        rule_id: Optional[int] = None,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None
    ) -> Alert:
        alert = Alert(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            rule_id=rule_id,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            metric_name=metric_name,
            metric_value=metric_value,
            message=message
        )
        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)
        return alert

    def list_alerts(
        self,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Alert]:
        query = self.session.query(Alert)
        if organization_id:
            query = query.filter(Alert.organization_id == organization_id)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        return query.order_by(Alert.triggered_at.desc()).all()

    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.session.get(Alert, alert_id)
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(alert)
        return alert

    def check_and_fire_alerts(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: str,
        metrics: Dict[str, float]
    ) -> List[Alert]:
        fired = []
        
        rules = self.session.query(AlertRule).filter(
            AlertRule.organization_id == organization_id,
            AlertRule.entity_type == entity_type,
            AlertRule.enabled == True
        ).all()
        
        for rule in rules:
            metric_value = metrics.get(rule.metric_name)
            if metric_value is None:
                continue
            
            should_fire = False
            if rule.condition == "gt" and metric_value > rule.threshold:
                should_fire = True
            elif rule.condition == "lt" and metric_value < rule.threshold:
                should_fire = True
            elif rule.condition == "eq" and abs(metric_value - rule.threshold) < 0.001:
                should_fire = True
            
            if should_fire:
                existing = self.session.query(Alert).filter(
                    Alert.rule_id == rule.id,
                    Alert.entity_id == entity_id,
                    Alert.status == "firing"
                ).first()
                
                if not existing:
                    alert = self.create_alert(
                        organization_id=organization_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        severity=rule.severity,
                        message=f"{rule.name}: {rule.metric_name} {rule.condition} {rule.threshold} (current: {metric_value})",
                        rule_id=rule.id,
                        metric_name=rule.metric_name,
                        metric_value=metric_value
                    )
                    fired.append(alert)
        
        return fired


class MetricService:
    def __init__(self, session: Session):
        self.session = session

    def record_metric(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None
    ) -> MetricSample:
        sample = MetricSample(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow()
        )
        self.session.add(sample)
        self.session.commit()
        return sample

    def get_metrics(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval_minutes: int = 5
    ) -> List[MetricSample]:
        query = self.session.query(MetricSample).filter(
            MetricSample.entity_type == entity_type,
            MetricSample.entity_id == entity_id,
            MetricSample.metric_name == metric_name
        )
        
        if start_time:
            query = query.filter(MetricSample.timestamp >= start_time)
        if end_time:
            query = query.filter(MetricSample.timestamp <= end_time)
        
        return query.order_by(MetricSample.timestamp.desc()).limit(1000).all()


class BackupService:
    def __init__(self, session: Session):
        self.session = session

    def create_backup(
        self,
        organization_id: int,
        vm_id: int,
        backup_type: str = "full"
    ) -> BackupJob:
        job = BackupJob(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            vm_id=vm_id,
            backup_type=backup_type,
            status="pending"
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def update_backup_status(
        self,
        job_id: int,
        status: str,
        backup_size_gb: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[BackupJob]:
        job = self.session.get(BackupJob, job_id)
        if not job:
            return None
        
        job.status = status
        if status == "running":
            job.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            job.completed_at = datetime.utcnow()
        if backup_size_gb is not None:
            job.backup_size_gb = backup_size_gb
        if error_message:
            job.error_message = error_message
        
        self.session.commit()
        self.session.refresh(job)
        return job

    def list_backups(
        self,
        organization_id: Optional[int] = None,
        vm_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[BackupJob]:
        query = self.session.query(BackupJob)
        if organization_id:
            query = query.filter(BackupJob.organization_id == organization_id)
        if vm_id:
            query = query.filter(BackupJob.vm_id == vm_id)
        if status:
            query = query.filter(BackupJob.status == status)
        return query.order_by(BackupJob.created_at.desc()).all()


class ServiceCatalogService:
    def __init__(self, session: Session):
        self.session = session

    def create_catalog_item(
        self,
        organization_id: int,
        name: str,
        specs: Dict[str, Any],
        category: str = "standard",
        description: Optional[str] = None
    ) -> ServiceCatalog:
        item = ServiceCatalog(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            name=name,
            category=category,
            description=description,
            specs=specs
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def list_catalog_items(
        self,
        organization_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[ServiceCatalog]:
        query = self.session.query(ServiceCatalog)
        if organization_id:
            query = query.filter(
                ServiceCatalog.organization_id == organization_id,
                ServiceCatalog.is_public == True
            )
        else:
            query = query.filter(ServiceCatalog.is_public == True)
        if category:
            query = query.filter(ServiceCatalog.category == category)
        return query.order_by(ServiceCatalog.usage_count.desc()).all()
