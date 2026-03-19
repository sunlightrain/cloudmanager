import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.tasks.celery_app import celery_app, TaskResult
from app.core.vsphere import get_vsphere_client, VSphereOperationError

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="vm_tasks.create_vm")
def create_vm_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_config: Dict[str, Any],
    datacenter: str,
    cluster: str,
    resource_pool: str
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Starting VM creation task: {task_id}, VM: {vm_config.get('name')}")
    
    try:
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "step": "connecting_vcenter"}
        )
        
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            self.update_state(
                state="PROGRESS",
                meta={"progress": 30, "step": "preparing_config"}
            )
            
            dc = client.get_datacenter(datacenter)
            if not dc:
                raise VSphereOperationError(f"Datacenter {datacenter} not found")
            
            cluster_obj = client.get_cluster(cluster, datacenter)
            if not cluster_obj:
                raise VSphereOperationError(f"Cluster {cluster} not found")
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "step": "creating_vm"}
            )
            
            vm_folder = dc.vmFolder
            resource_pool_obj = cluster_obj.resourcePool
            
            from pyVmomi import vim
            
            vm_create_spec = vim.vm.ConfigSpec()
            vm_create_spec.name = vm_config['name']
            vm_create_spec.memoryMB = vm_config.get('memory_mb', 1024)
            vm_create_spec.numCPUs = vm_config.get('cpu', 1)
            vm_create_spec.guestId = vm_config.get('guest_id', 'otherLinuxGuest')
            vm_create_spec.annotation = vm_config.get('annotation', '')
            
            if 'disk_gb' in vm_config:
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                disk_spec.device = vim.vm.device.VirtualDisk()
                disk_spec.device.key = -1
                disk_spec.device.backing = vim.vm.device.VirtualDisk.LocalPMEMBackingInfo()
                disk_spec.device.capacityInKB = vm_config['disk_gb'] * 1024 * 1024
                vm_create_spec.deviceChange = [disk_spec]
            
            task = vm_folder.CreateVM_Task(spec=vm_create_spec, pool=resource_pool_obj)
            
            from pyVmomi import vim
            while task.info.state == vim.TaskInfo.State.running:
                pass
            
            if task.info.state == vim.TaskInfo.State.success:
                vm = client.get_vm(vm_config['name'], datacenter)
                result = {
                    "task_id": task_id,
                    "status": "success",
                    "vm_id": vm._GetMoId() if vm else None,
                    "vm_name": vm_config['name'],
                    "progress": 100
                }
                logger.info(f"VM created successfully: {task_id}")
                return result
            else:
                error_msg = task.info.error.localizedMessage if hasattr(task.info.error, 'localizedMessage') else str(task.info.error)
                raise VSphereOperationError(f"Failed to create VM: {error_msg}")
    
    except Exception as e:
        logger.error(f"Failed to create VM: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "progress": 0
        }


@celery_app.task(bind=True, name="vm_tasks.power_operation")
def vm_power_operation_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    operation: str,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"VM power operation: {task_id}, vm_id: {vm_id}, operation: {operation}")
    
    try:
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vm_obj = client.get_vm_by_id(vm_id)
            if not vm_obj:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            vms = client.get_all_vms(datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            if operation == "start":
                client.power_on_vm(vm)
            elif operation == "stop":
                client.power_off_vm(vm)
            elif operation == "restart":
                client.power_off_vm(vm)
                client.power_on_vm(vm)
            else:
                raise VSphereOperationError(f"Unknown operation: {operation}")
            
            return {
                "task_id": task_id,
                "status": "success",
                "vm_id": vm_id,
                "operation": operation,
                "new_status": client.get_vm_by_id(vm_id)['status'] if client.get_vm_by_id(vm_id) else "unknown"
            }
    
    except Exception as e:
        logger.error(f"Power operation failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="vm_tasks.delete_vm")
def delete_vm_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"VM delete task: {task_id}, vm_id: {vm_id}")
    
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
            
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                while task.info.state == "running":
                    pass
            
            task = vm.Destroy_Task()
            while task.info.state == "running":
                pass
            
            if task.info.state == "success":
                return {
                    "task_id": task_id,
                    "status": "success",
                    "vm_id": vm_id
                }
            else:
                raise VSphereOperationError("Failed to delete VM")
    
    except Exception as e:
        logger.error(f"Delete VM failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="vm_tasks.clone_vm")
def clone_vm_task(
    self,
    vcenter_config: Dict[str, Any],
    source_vm_id: str,
    clone_name: str,
    datacenter: str,
    cluster: str,
    resource_pool: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"VM clone task: {task_id}, source: {source_vm_id}, clone: {clone_name}")
    
    try:
        self.update_state(
            state="PROGRESS",
            meta={"progress": 20, "step": "preparing_clone"}
        )
        
        with get_vsphere_client(
            host=vcenter_config['host'],
            user=vcenter_config['username'],
            password=vcenter_config['password'],
            port=vcenter_config.get('port', 443),
            datacenter=datacenter
        ) as client:
            vms = client.get_all_vms(datacenter)
            source_vm = None
            for v in vms:
                if v._GetMoId() == source_vm_id:
                    source_vm = v
                    break
            
            if not source_vm:
                raise VSphereOperationError(f"Source VM {source_vm_id} not found")
            
            dc = client.get_datacenter(datacenter)
            cluster_obj = client.get_cluster(cluster, datacenter)
            
            if not cluster_obj:
                raise VSphereOperationError(f"Cluster {cluster} not found")
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 50, "step": "creating_clone"}
            )
            
            clone_spec = vim.vm.CloneSpec()
            clone_spec.powerOn = False
            
            if resource_pool:
                resource_pool_obj = cluster_obj.resourcePool
                clone_spec.location = vim.vm.RelocateSpec()
                clone_spec.location.pool = resource_pool_obj
            
            task = source_vm.Clone_Task(folder=dc.vmFolder, name=clone_name, spec=clone_spec)
            
            while task.info.state == "running":
                pass
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 90, "step": "completed"}
            )
            
            if task.info.state == "success":
                cloned_vm = client.get_vm(clone_name, datacenter)
                return {
                    "task_id": task_id,
                    "status": "success",
                    "source_vm_id": source_vm_id,
                    "cloned_vm_id": cloned_vm._GetMoId() if cloned_vm else None,
                    "cloned_vm_name": clone_name,
                    "progress": 100
                }
            else:
                raise VSphereOperationError("Clone operation failed")
    
    except Exception as e:
        logger.error(f"Clone VM failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="vm_tasks.resize_resources")
def resize_vm_resources_task(
    self,
    vcenter_config: Dict[str, Any],
    vm_id: str,
    cpu: Optional[int] = None,
    memory_mb: Optional[int] = None,
    datacenter: Optional[str] = None
) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"VM resize task: {task_id}, vm_id: {vm_id}")
    
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
            
            config_spec = vim.vm.ConfigSpec()
            changes = []
            
            if cpu is not None:
                config_spec.numCPUs = cpu
                changes.append(f"cpu:{vm.config.hardware.numCPU}->{cpu}")
            
            if memory_mb is not None:
                config_spec.memoryMB = memory_mb
                changes.append(f"memory:{vm.config.hardware.memoryMB}->{memory_mb}")
            
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.RECTask(config_spec)
            else:
                task = vm.Reconfigure(config_spec)
            
            while task.info.state == "running":
                pass
            
            if task.info.state == "success":
                return {
                    "task_id": task_id,
                    "status": "success",
                    "vm_id": vm_id,
                    "changes": changes
                }
            else:
                raise VSphereOperationError("Resize operation failed")
    
    except Exception as e:
        logger.error(f"Resize VM failed: {e}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


import vim
