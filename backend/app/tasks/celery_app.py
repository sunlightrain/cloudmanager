from celery import Celery
from typing import Optional, Dict, Any
import logging

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vsphere_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0" if hasattr(settings, 'REDIS_HOST') else "memory://",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1" if hasattr(settings, 'REDIS_HOST') else "cache+memory://",
    include=[
        "app.tasks.vm_tasks",
        "app.tasks.snapshot_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "app.tasks.vm_tasks.*": {"queue": "vm_operations"},
        "app.tasks.snapshot_tasks.*": {"queue": "snapshot_operations"},
    },
)


class TaskResult:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._result = None
    
    @property
    def status(self) -> str:
        if self._result is None:
            try:
                result = celery_app.AsyncResult(self.task_id)
                return result.state
            except:
                return "PENDING"
        return "SUCCESS"
    
    @property
    def info(self) -> Optional[Dict[str, Any]]:
        try:
            result = celery_app.AsyncResult(self.task_id)
            if result.ready():
                return result.result
            elif result.state == "PROGRESS":
                return result.info
        except:
            pass
        return None
    
    @property
    def progress(self) -> Optional[int]:
        try:
            result = celery_app.AsyncResult(self.task_id)
            if result.state == "PROGRESS" and isinstance(result.info, dict):
                return result.info.get("progress", 0)
        except:
            pass
        return None
    
    def wait(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        try:
            result = celery_app.AsyncResult(self.task_id)
            return result.get(timeout=timeout)
        except Exception as e:
            return {"error": str(e)}
    
    def revoke(self, terminate: bool = False):
        try:
            result = celery_app.AsyncResult(self.task_id)
            result.revoke(terminate=terminate)
        except:
            pass


logger = logging.getLogger(__name__)
