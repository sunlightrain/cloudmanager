import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.backup import BackupPolicy, BackupJob, BackupFile

logger = logging.getLogger(__name__)


class BackupService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_backup_policies(self, tenant_id: int = None) -> List[BackupPolicy]:
        query = self.session.query(BackupPolicy)
        if tenant_id:
            query = query.filter(BackupPolicy.tenant_id == tenant_id)
        return query.all()
    
    def get_backup_policy(self, policy_id: int) -> Optional[BackupPolicy]:
        return self.session.query(BackupPolicy).filter(BackupPolicy.id == policy_id).first()
    
    def create_backup_policy(
        self,
        name: str,
        tenant_id: int,
        target_type: str,
        target_ids: List[str] = None,
        backup_type: str = "full",
        schedule: str = "daily",
        retention_count: int = 7
    ) -> BackupPolicy:
        next_backup = self._calculate_next_backup(schedule)
        
        policy = BackupPolicy(
            name=name,
            tenant_id=tenant_id,
            target_type=target_type,
            target_ids=json.dumps(target_ids) if target_ids else None,
            backup_type=backup_type,
            schedule=schedule,
            retention_count=retention_count,
            next_backup_at=next_backup
        )
        self.session.add(policy)
        self.session.commit()
        self.session.refresh(policy)
        return policy
    
    def update_backup_policy(
        self,
        policy_id: int,
        name: str = None,
        backup_type: str = None,
        schedule: str = None,
        retention_count: int = None,
        is_active: bool = None
    ) -> Optional[BackupPolicy]:
        policy = self.get_backup_policy(policy_id)
        if not policy:
            return None
        
        if name is not None:
            policy.name = name
        if backup_type is not None:
            policy.backup_type = backup_type
        if schedule is not None:
            policy.schedule = schedule
            policy.next_backup_at = self._calculate_next_backup(schedule)
        if retention_count is not None:
            policy.retention_count = retention_count
        if is_active is not None:
            policy.is_active = is_active
        
        self.session.commit()
        return policy
    
    def delete_backup_policy(self, policy_id: int) -> bool:
        policy = self.get_backup_policy(policy_id)
        if not policy:
            return False
        self.session.delete(policy)
        self.session.commit()
        return True
    
    def _calculate_next_backup(self, schedule: str) -> datetime:
        now = datetime.utcnow()
        if schedule == "daily":
            return now + timedelta(days=1)
        elif schedule == "weekly":
            return now + timedelta(weeks=1)
        elif schedule == "monthly":
            return now + timedelta(days=30)
        return now + timedelta(days=1)
    
    def get_due_backups(self) -> List[BackupPolicy]:
        now = datetime.utcnow()
        return self.session.query(BackupPolicy).filter(
            BackupPolicy.is_active == True,
            BackupPolicy.next_backup_at <= now
        ).all()
    
    def create_backup_job(
        self,
        policy_id: int = None,
        resource_type: str = None,
        resource_id: str = None,
        backup_type: str = "full"
    ) -> BackupJob:
        job = BackupJob(
            policy_id=policy_id,
            resource_type=resource_type,
            resource_id=resource_id,
            backup_type=backup_type,
            status="pending",
            started_at=datetime.utcnow()
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def execute_backup(self, job: BackupJob) -> Dict[str, Any]:
        from app.services.vm_service import VMService
        
        try:
            job.status = "running"
            self.session.commit()
            
            if job.resource_type == "vm":
                result = self._backup_vm(job.resource_id, job.backup_type)
            else:
                raise ValueError(f"Unsupported resource type: {job.resource_type}")
            
            job.status = "completed"
            job.size_bytes = result.get("size_bytes", 0)
            job.backup_path = result.get("path", "")
            job.completed_at = datetime.utcnow()
            self.session.commit()
            
            if job.policy_id:
                policy = self.get_backup_policy(job.policy_id)
                if policy:
                    policy.last_backup_at = datetime.utcnow()
                    policy.next_backup_at = self._calculate_next_backup(policy.schedule)
                    self.session.commit()
            
            self._cleanup_old_backups(job.policy_id, job.resource_id)
            
            return {"success": True, "job_id": job.id}
        
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.session.commit()
            return {"success": False, "error": str(e)}
    
    def _backup_vm(self, vm_id: str, backup_type: str) -> Dict[str, Any]:
        return {
            "path": f"/backups/vm_{vm_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "size_bytes": 1024 * 1024 * 1024 * 10
        }
    
    def _cleanup_old_backups(self, policy_id: int, resource_id: str):
        if not policy_id:
            return
        
        policy = self.get_backup_policy(policy_id)
        if not policy:
            return
        
        retention_count = policy.retention_count
        
        old_jobs = self.session.query(BackupJob).filter(
            BackupJob.policy_id == policy_id,
            BackupJob.resource_id == resource_id,
            BackupJob.status == "completed"
        ).order_by(BackupJob.completed_at.desc()).offset(retention_count).all()
        
        for job in old_jobs:
            job.status = "expired"
            self.session.commit()
    
    def get_backup_jobs(
        self,
        policy_id: int = None,
        resource_type: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[BackupJob]:
        query = self.session.query(BackupJob)
        if policy_id:
            query = query.filter(BackupJob.policy_id == policy_id)
        if resource_type:
            query = query.filter(BackupJob.resource_type == resource_type)
        if status:
            query = query.filter(BackupJob.status == status)
        return query.order_by(BackupJob.created_at.desc()).limit(limit).all()
    
    def restore_backup(
        self,
        job_id: int,
        restore_type: str = "original",
        target_host_id: str = None
    ) -> Dict[str, Any]:
        job = self.session.query(BackupJob).filter(BackupJob.id == job_id).first()
        if not job:
            return {"success": False, "error": "Backup job not found"}
        
        if job.status != "completed":
            return {"success": False, "error": "Backup not completed"}
        
        try:
            if job.resource_type == "vm":
                result = self._restore_vm(job, restore_type, target_host_id)
                return {"success": True, "message": "Restore initiated", "result": result}
            else:
                return {"success": False, "error": f"Unsupported resource type: {job.resource_type}"}
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _restore_vm(self, job: BackupJob, restore_type: str, target_host_id: str = None) -> Dict[str, Any]:
        return {
            "restore_type": restore_type,
            "target_host": target_host_id,
            "backup_path": job.backup_path
        }
    
    def get_backup_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        jobs = self.session.query(BackupJob).filter(
            BackupJob.resource_type == resource_type,
            BackupJob.resource_id == resource_id,
            BackupJob.status == "completed"
        ).order_by(BackupJob.completed_at.desc()).limit(limit).all()
        
        return [
            {
                "id": job.id,
                "backup_type": job.backup_type,
                "status": job.status,
                "size_bytes": job.size_bytes,
                "backup_path": job.backup_path,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]