import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app
from app.core.vsphere import get_vsphere_client, VSphereOperationError

logger = logging.getLogger(__name__)

SNAPSHOT_MAX_AGE_HOURS = 72


@celery_app.task(bind=True, name="snapshot_tasks.create_snapshot")
def create_snapshot_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    snapshot_name: str,
    description: str = "",
    memory: bool = False,
    quiesce: bool = False,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Create snapshot task: {task_id}, vm_id: {vm_id}, name: {snapshot_name}")
    
    try:
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vms = client.get_all_vms(datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            existing_snapshots = client.get_vm_snapshots(vm)
            for snap in existing_snapshots:
                if snap.get('created'):
                    created_time = datetime.fromisoformat(snap['created'].replace('Z', '+00:00'))
                    age_hours = (datetime.now() - created_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours > SNAPSHOT_MAX_AGE_HOURS:
                        raise VSphereOperationError(
                            f"Existing snapshot '{snap['name']}' is older than {SNAPSHOT_MAX_AGE_HOURS} hours. "
                            "Please delete old snapshots before creating new ones."
                        )
            
            snapshot_id = client.create_snapshot(vm, snapshot_name, description, memory, quiesce)
            
            return {
                "task_id": task_id,
                "status": "success",
                "vm_id": vm_id,
                "snapshot_name": snapshot_name,
                "snapshot_id": snapshot_id
            }
    
    except Exception as e:
        logger.error(f"Create snapshot failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="snapshot_tasks.delete_snapshot")
def delete_snapshot_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    snapshot_id: int,
    remove_children: bool = False,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Delete snapshot task: {task_id}, vm_id: {vm_id}, snapshot_id: {snapshot_id}")
    
    try:
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vms = client.get_all_vms(datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            success = client.remove_snapshot(vm, snapshot_id, remove_children)
            
            if success:
                return {
                    "task_id": task_id,
                    "status": "success",
                    "vm_id": vm_id,
                    "snapshot_id": snapshot_id
                }
            else:
                raise VSphereOperationError(f"Snapshot {snapshot_id} not found")
    
    except Exception as e:
        logger.error(f"Delete snapshot failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="snapshot_tasks.revert_snapshot")
def revert_snapshot_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    snapshot_id: int,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Revert snapshot task: {task_id}, vm_id: {vm_id}, snapshot_id: {snapshot_id}")
    
    try:
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vms = client.get_all_vms(datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            success = client.revert_to_snapshot(vm, snapshot_id)
            
            if success:
                return {
                    "task_id": task_id,
                    "status": "success",
                    "vm_id": vm_id,
                    "snapshot_id": snapshot_id
                }
            else:
                raise VSphereOperationError(f"Snapshot {snapshot_id} not found")
    
    except Exception as e:
        logger.error(f"Revert snapshot failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="snapshot_tasks.delete_old_snapshots")
def delete_old_snapshots_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    max_age_hours: int = SNAPSHOT_MAX_AGE_HOURS,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Delete old snapshots task: {task_id}, vm_id: {vm_id}")
    
    try:
        deleted_count = 0
        
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vms = client.get_all_vms(datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            snapshots = client.get_vm_snapshots(vm)
            
            for snap in snapshots:
                if snap.get('created'):
                    created_time = datetime.fromisoformat(snap['created'].replace('Z', '+00:00'))
                    age_hours = (datetime.now() - created_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        client.remove_snapshot(vm, snap['snapshot_id'], remove_children=True)
                        deleted_count += 1
            
            return {
                "task_id": task_id,
                "status": "success",
                "vm_id": vm_id,
                "deleted_count": deleted_count
            }
    
    except Exception as e:
        logger.error(f"Delete old snapshots failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }
