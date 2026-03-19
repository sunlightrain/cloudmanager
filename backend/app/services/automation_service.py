import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from croniter import croniter
from sqlalchemy.orm import Session
from app.models.automation import ScheduledTask, ServiceTemplate, VMInitConfig

logger = logging.getLogger(__name__)


class AutomationService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_scheduled_tasks(self, task_type: str = None) -> List[ScheduledTask]:
        query = self.session.query(ScheduledTask)
        if task_type:
            query = query.filter(ScheduledTask.task_type == task_type)
        return query.all()
    
    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        return self.session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    
    def create_scheduled_task(
        self,
        name: str,
        task_type: str,
        target_type: str,
        cron_expression: str,
        target_ids: List[str] = None,
        action_params: Dict[str, Any] = None,
        is_active: bool = True
    ) -> ScheduledTask:
        next_run = self._calculate_next_run(cron_expression)
        
        task = ScheduledTask(
            name=name,
            task_type=task_type,
            target_type=target_type,
            target_ids=json.dumps(target_ids) if target_ids else None,
            cron_expression=cron_expression,
            action_params=json.dumps(action_params) if action_params else None,
            is_active=is_active,
            next_run_at=next_run
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def update_scheduled_task(
        self,
        task_id: int,
        name: str = None,
        cron_expression: str = None,
        target_ids: List[str] = None,
        action_params: Dict[str, Any] = None,
        is_active: bool = None
    ) -> Optional[ScheduledTask]:
        task = self.get_task(task_id)
        if not task:
            return None
        
        if name is not None:
            task.name = name
        if cron_expression is not None:
            task.cron_expression = cron_expression
            task.next_run_at = self._calculate_next_run(cron_expression)
        if target_ids is not None:
            task.target_ids = json.dumps(target_ids)
        if action_params is not None:
            task.action_params = json.dumps(action_params)
        if is_active is not None:
            task.is_active = is_active
        
        self.session.commit()
        return task
    
    def delete_scheduled_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        self.session.delete(task)
        self.session.commit()
        return True
    
    def _calculate_next_run(self, cron_expr: str) -> Optional[datetime]:
        try:
            cron = croniter(cron_expr, datetime.utcnow())
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression: {cron_expr}: {e}")
            return None
    
    def get_due_tasks(self) -> List[ScheduledTask]:
        now = datetime.utcnow()
        return self.session.query(ScheduledTask).filter(
            ScheduledTask.is_active == True,
            ScheduledTask.next_run_at <= now
        ).all()
    
    def execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        from app.services.vm_service import VMService
        
        target_ids = json.loads(task.target_ids) if task.target_ids else []
        action_params = json.loads(task.action_params) if task.action_params else {}
        
        results = []
        
        if task.task_type == "vm_power":
            action = action_params.get("action", "power_on")
            for vm_id in target_ids:
                try:
                    vm_service = VMService(self.session)
                    if action == "power_on":
                        result = await vm_service.power_on(vm_id)
                    elif action == "power_off":
                        result = await vm_service.power_off(vm_id)
                    results.append({"vm_id": vm_id, "success": True})
                except Exception as e:
                    results.append({"vm_id": vm_id, "success": False, "error": str(e)})
        
        elif task.task_type == "snapshot_cleanup":
            keep_count = action_params.get("keep_count", 0)
            for vm_id in target_ids:
                try:
                    vm_service = VMService(self.session)
                    result = await vm_service.cleanup_snapshots(vm_id, keep_count)
                    results.append({"vm_id": vm_id, "success": True})
                except Exception as e:
                    results.append({"vm_id": vm_id, "success": False, "error": str(e)})
        
        task.last_run_at = datetime.utcnow()
        task.next_run_at = self._calculate_next_run(task.cron_expression)
        self.session.commit()
        
        return {"success": True, "results": results}
    
    def get_service_templates(self, category: str = None) -> List[ServiceTemplate]:
        query = self.session.query(ServiceTemplate).filter(ServiceTemplate.is_active == True)
        if category:
            query = query.filter(ServiceTemplate.category == category)
        return query.all()
    
    def get_service_template(self, template_id: int) -> Optional[ServiceTemplate]:
        return self.session.query(ServiceTemplate).filter(ServiceTemplate.id == template_id).first()
    
    def create_service_template(
        self,
        name: str,
        category: str,
        cpu: int,
        memory_mb: int,
        disk_gb: int,
        os_type: str,
        price: float = None
    ) -> ServiceTemplate:
        template = ServiceTemplate(
            name=name,
            category=category,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            os_type=os_type,
            price=price
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template
    
    def get_vm_init_config(self, vm_id: int) -> Optional[VMInitConfig]:
        return self.session.query(VMInitConfig).filter(VMInitConfig.vm_id == vm_id).first()
    
    def create_vm_init_config(
        self,
        vm_id: int,
        hostname: str = None,
        ip_address: str = None,
        subnet_mask: str = None,
        gateway: str = None,
        dns_servers: List[str] = None,
        dns_suffix: str = None,
        custom_script: str = None,
        password: str = None
    ) -> VMInitConfig:
        config = VMInitConfig(
            vm_id=vm_id,
            hostname=hostname,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            gateway=gateway,
            dns_servers=json.dumps(dns_servers) if dns_servers else None,
            dns_suffix=dns_suffix,
            custom_script=custom_script,
            password=password
        )
        self.session.add(config)
        self.session.commit()
        self.session.refresh(config)
        return config
    
    def generate_cloud_init_config(self, config: VMInitConfig) -> str:
        cloud_config = {
            "hostname": config.hostname,
            "fqdn": f"{config.hostname}.{config.dns_suffix}" if config.dns_suffix else config.hostname,
        }
        
        if config.ip_address:
            network_config = {
                "version": 2,
                "ethernets": {
                    "eth0": {
                        "addresses": [f"{config.ip_address}/{self._subnet_to_cidr(config.subnet_mask)}"],
                        "gateway": config.gateway,
                        "nameservers": {
                            "addresses": json.loads(config.dns_servers) if config.dns_servers else []
                        }
                    }
                }
            }
            cloud_config["network"] = network_config
        
        if config.password:
            cloud_config["password"] = config.password
            cloud_config["chpasswd"] = {"expire": False}
        
        if config.custom_script:
            cloud_config["runcmd"] = [config.custom_script]
        
        return json.dumps(cloud_config, indent=2)
    
    def _subnet_to_cidr(self, subnet_mask: str) -> int:
        if not subnet_mask:
            return 24
        parts = subnet_mask.split(".")
        cidr = sum(int(part) << (8 * (3 - i)) for i, part in enumerate(parts))
        return bin(cidr).count("1")
