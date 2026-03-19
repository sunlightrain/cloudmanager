import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.monitoring import AlertRule, Alert, NotificationChannel, MetricDataPoint

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_alert_rules(self, resource_type: str = None) -> List[AlertRule]:
        query = self.session.query(AlertRule)
        if resource_type:
            query = query.filter(AlertRule.resource_type == resource_type)
        return query.all()
    
    def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        return self.session.query(AlertRule).filter(AlertRule.id == rule_id).first()
    
    def create_alert_rule(
        self,
        name: str,
        resource_type: str,
        metric: str,
        condition: str,
        threshold: float,
        severity: str = "warning",
        duration: int = 0
    ) -> AlertRule:
        rule = AlertRule(
            name=name,
            resource_type=resource_type,
            metric=metric,
            condition=condition,
            threshold=threshold,
            severity=severity,
            duration=duration
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule
    
    def update_alert_rule(
        self,
        rule_id: int,
        name: str = None,
        condition: str = None,
        threshold: float = None,
        severity: str = None,
        duration: int = None,
        is_active: bool = None
    ) -> Optional[AlertRule]:
        rule = self.get_alert_rule(rule_id)
        if not rule:
            return None
        
        if name is not None:
            rule.name = name
        if condition is not None:
            rule.condition = condition
        if threshold is not None:
            rule.threshold = threshold
        if severity is not None:
            rule.severity = severity
        if duration is not None:
            rule.duration = duration
        if is_active is not None:
            rule.is_active = is_active
        
        self.session.commit()
        return rule
    
    def delete_alert_rule(self, rule_id: int) -> bool:
        rule = self.get_alert_rule(rule_id)
        if not rule:
            return False
        self.session.delete(rule)
        self.session.commit()
        return True
    
    def get_active_alerts(self, tenant_id: int = None) -> List[Alert]:
        query = self.session.query(Alert).filter(Alert.status == "active")
        if tenant_id:
            query = query.filter(Alert.tenant_id == tenant_id)
        return query.order_by(Alert.triggered_at.desc()).all()
    
    def get_alerts(
        self,
        tenant_id: int = None,
        status: str = None,
        severity: str = None,
        limit: int = 100
    ) -> List[Alert]:
        query = self.session.query(Alert)
        if tenant_id:
            query = query.filter(Alert.tenant_id == tenant_id)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        return query.order_by(Alert.triggered_at.desc()).limit(limit).all()
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> Optional[Alert]:
        alert = self.session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        self.session.commit()
        return alert
    
    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.session.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        self.session.commit()
        return alert
    
    def check_and_create_alerts(self, resource_type: str, resource_id: str, tenant_id: int, metrics: Dict[str, float]) -> List[Alert]:
        rules = self.session.query(AlertRule).filter(
            AlertRule.resource_type == resource_type,
            AlertRule.is_active == True
        ).all()
        
        new_alerts = []
        for rule in rules:
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue
            
            if self._evaluate_condition(rule.condition, metric_value, rule.threshold):
                existing = self.session.query(Alert).filter(
                    Alert.rule_id == rule.id,
                    Alert.resource_id == resource_id,
                    Alert.status == "active"
                ).first()
                
                if not existing:
                    alert = Alert(
                        rule_id=rule.id,
                        tenant_id=tenant_id,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        metric=rule.metric,
                        value=metric_value,
                        threshold=rule.threshold,
                        severity=rule.severity
                    )
                    self.session.add(alert)
                    new_alerts.append(alert)
        
        if new_alerts:
            self.session.commit()
            for alert in new_alerts:
                self._send_notifications(alert)
        
        return new_alerts
    
    def _evaluate_condition(self, condition: str, value: float, threshold: float) -> bool:
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        return False
    
    def _send_notifications(self, alert: Alert):
        channels = self.session.query(NotificationChannel).filter(
            NotificationChannel.is_active == True
        ).all()
        
        for channel in channels:
            try:
                if channel.type == "webhook":
                    self._send_webhook(channel.config, alert)
                elif channel.type == "email":
                    self._send_email(channel.config, alert)
                elif channel.type == "wechat":
                    self._send_wechat(channel.config, alert)
                elif channel.type == "dingtalk":
                    self._send_dingtalk(channel.config, alert)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.type}: {e}")
    
    def _send_webhook(self, config: str, alert: Alert):
        import requests
        webhook_url = config
        payload = {
            "alert_id": alert.id,
            "severity": alert.severity,
            "resource_type": alert.resource_type,
            "resource_id": alert.resource_id,
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold,
            "message": f"{alert.metric} {alert.value} {alert.severity}"
        }
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
    
    def _send_email(self, config: str, alert: Alert):
        import smtplib
        from email.mime.text import MIMEText
        
        email_config = json.loads(config)
        msg = MIMEText(f"Alert: {alert.metric} = {alert.value} (threshold: {alert.threshold})")
        msg["Subject"] = f"[{alert.severity.upper()}] Cloud Manager Alert"
        msg["From"] = email_config.get("from")
        msg["To"] = email_config.get("to")
        
        with smtplib.SMTP(email_config.get("smtp_host"), email_config.get("smtp_port", 587)) as server:
            server.starttls()
            server.login(email_config.get("username"), email_config.get("password"))
            server.send_message(msg)
    
    def _send_wechat(self, config: str, alert: Alert):
        import requests
        wechat_config = json.loads(config)
        webhook_url = wechat_config.get("webhook_url")
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"[{alert.severity}] {alert.resource_type}: {alert.metric} = {alert.value}"
            }
        }
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"WeChat notification failed: {e}")
    
    def _send_dingtalk(self, config: str, alert: Alert):
        import requests
        dingtalk_config = json.loads(config)
        webhook_url = dingtalk_config.get("webhook_url")
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"[{alert.severity}] {alert.resource_type}: {alert.metric} = {alert.value}"
            }
        }
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"DingTalk notification failed: {e}")
    
    def record_metric(
        self,
        resource_type: str,
        resource_id: str,
        metric: str,
        value: float
    ):
        dp = MetricDataPoint(
            resource_type=resource_type,
            resource_id=resource_id,
            metric=metric,
            value=value
        )
        self.session.add(dp)
        self.session.commit()
    
    def get_metrics(
        self,
        resource_type: str,
        resource_id: str,
        metric: str,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[MetricDataPoint]:
        query = self.session.query(MetricDataPoint).filter(
            MetricDataPoint.resource_type == resource_type,
            MetricDataPoint.resource_id == resource_id,
            MetricDataPoint.metric == metric
        )
        
        if start_time:
            query = query.filter(MetricDataPoint.timestamp >= start_time)
        if end_time:
            query = query.filter(MetricDataPoint.timestamp <= end_time)
        
        return query.order_by(MetricDataPoint.timestamp.desc()).limit(limit).all()
    
    def get_notification_channels(self) -> List[NotificationChannel]:
        return self.session.query(NotificationChannel).all()
    
    def create_notification_channel(
        self,
        name: str,
        channel_type: str,
        config: Dict[str, Any]
    ) -> NotificationChannel:
        channel = NotificationChannel(
            name=name,
            type=channel_type,
            config=json.dumps(config)
        )
        self.session.add(channel)
        self.session.commit()
        self.session.refresh(channel)
        return channel