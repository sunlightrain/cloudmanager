from typing import Optional, List, Dict, Any, Callable
from app.core.config import get_settings
from datetime import datetime
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

settings = get_settings()

try:
    from pyvim.connect import SmartConnect, Disconnect
    from pyvim import folder
    PYVIMOMI_AVAILABLE = True
except ImportError:
    PYVIMOMI_AVAILABLE = False
    SmartConnect = None
    Disconnect = None
    folder = None


class VSphereConnectionError(Exception):
    pass


class VSphereOperationError(Exception):
    pass


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            raise VSphereOperationError(f"Failed after {max_attempts} attempts: {last_error}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise VSphereOperationError(f"Failed after {max_attempts} attempts: {last_error}")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


class VSphereClient:
    _instance: Optional["VSphereClient"] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._client = None
        self._connected = False
        self._host = None
        self._username = None
        self._password = None
        self._port = 443
        self._connection_time = None
    
    @classmethod
    async def get_instance(cls) -> "VSphereClient":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_instance_sync(cls) -> "VSphereClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @with_retry(max_attempts=3, delay=1.0)
    async def connect(self, host: str, username: str, password: str, port: int = 443) -> bool:
        try:
            if PYVIMOMI_AVAILABLE and SmartConnect:
                self._client = SmartConnect(
                    host=host,
                    user=username,
                    pwd=password,
                    port=port
                )
            self._host = host
            self._username = username
            self._password = password
            self._port = port
            self._connected = True
            self._connection_time = datetime.utcnow()
            logger.info(f"Connected to vCenter {host}")
            return True
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to vCenter: {e}")
            raise VSphereConnectionError(f"Failed to connect to vCenter: {str(e)}")
    
    def connect_sync(self, host: str, username: str, password: str, port: int = 443) -> bool:
        try:
            if PYVIMOMI_AVAILABLE and SmartConnect:
                self._client = SmartConnect(
                    host=host,
                    user=username,
                    pwd=password,
                    port=port
                )
            self._host = host
            self._username = username
            self._password = password
            self._port = port
            self._connected = True
            self._connection_time = datetime.utcnow()
            logger.info(f"Connected to vCenter {host}")
            return True
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to vCenter: {e}")
            raise VSphereConnectionError(f"Failed to connect to vCenter: {str(e)}")
    
    @with_retry(max_attempts=3, delay=2.0)
    async def reconnect(self) -> bool:
        if self._host and self._username and self._password:
            return await self.connect(self._host, self._username, self._password, self._port)
        raise VSphereConnectionError("No previous connection credentials available")
    
    def reconnect_sync(self) -> bool:
        if self._host and self._username and self._password:
            return self.connect_sync(self._host, self._username, self._password, self._port)
        raise VSphereConnectionError("No previous connection credentials available")
    
    def disconnect(self):
        if self._client and PYVIMOMI_AVAILABLE and Disconnect:
            try:
                Disconnect(self._client)
            except Exception as e:
                logger.error(f"Error disconnecting from vCenter: {e}")
        self._client = None
        self._connected = False
        self._connection_time = None
        logger.info("Disconnected from vCenter")
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        return {
            "host": self._host,
            "port": self._port,
            "connected": self._connected,
            "connection_time": self._connection_time.isoformat() if self._connection_time else None
        }
    
    def _ensure_connected(self):
        if not self.is_connected:
            raise VSphereConnectionError("Not connected to vCenter")
    
    def _find_vm(self, vm_id: str):
        self._ensure_connected()
        content = self._client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm._GetMoId() == vm_id:
                return vm
        return None
    
    def _find_vm_by_name(self, name: str):
        self._ensure_connected()
        content = self._client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm.name == name:
                return vm
        return None
    
    def _find_host_by_id(self, host_id: str):
        self._ensure_connected()
        content = self._client.content
        hosts = content.rootFolder.childEntity[0].hostFolder.childEntity
        for host in hosts:
            if host._GetMoId() == host_id:
                return host
        return None
    
    def _find_datastore_by_id(self, datastore_id: str):
        self._ensure_connected()
        content = self._client.content
        datastores = content.rootFolder.childEntity[0].datastoreFolder.childEntity
        for ds in datastores:
            if ds._GetMoId() == datastore_id:
                return ds
        return None
    
    def _find_folder_by_id(self, folder_id: str):
        self._ensure_connected()
        content = self._client.content
        folders = content.rootFolder.childEntity[0].vmFolder.childEntity
        for folder in folders:
            if hasattr(folder, '_GetMoId') and folder._GetMoId() == folder_id:
                return folder
        return None
    
    def _find_snapshot_by_id(self, vm, snapshot_id: str):
        snapshot_info = vm.snapshot
        if not snapshot_info or not snapshot_info.rootSnapshotList:
            return None
        
        def find_snap(snapshots, snap_id):
            for snap in snapshots:
                if str(snap.id) == str(snap_id):
                    return snap
                if snap.childSnapshotList:
                    result = find_snap(snap.childSnapshotList, snap_id)
                    if result:
                        return result
            return None
        
        return find_snap(snapshot_info.rootSnapshotList, snapshot_id)
    
    def _wait_for_task(self, task, timeout: int = 300):
        if PYVIMOMI_AVAILABLE:
            from pyVmomi import vim
            while True:
                if task.info.state == vim.TaskInfo.State.success:
                    return task.info.result
                elif task.info.state == vim.TaskInfo.State.error:
                    raise VSphereOperationError(f"Task failed: {task.info.error}")
                import time
                time.sleep(1)
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_vms(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            vm_folder = content.rootFolder.childEntity[0].vmFolder
            vms = folder.InventoryFolder(vm_folder).childEntity
            
            result = []
            for vm in vms:
                try:
                    result.append({
                        "vm_id": vm._GetMoId(),
                        "name": vm.name,
                        "status": vm.runtime.powerState.value,
                        "cpu": vm.config.hardware.numCPU,
                        "memory_mb": vm.config.hardware.memoryMB,
                        "ip_address": vm.guest.ipAddress if vm.guest else None,
                        "host": vm.runtime.host.name if vm.runtime.host else None,
                        "datastore": ",".join([ds.name for ds in vm.config.datastore]) if vm.config.datastore else None,
                    })
                except Exception as e:
                    logger.warning(f"Error getting VM info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting VMs: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_vm_by_id(self, vm_id: str) -> Optional[Dict[str, Any]]:
        vm = self._find_vm(vm_id)
        if not vm:
            return None
        
        try:
            disk_info = []
            if vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if hasattr(device, 'capacityInKB') and device.capacityInKB:
                        disk_info.append({
                            "label": device.deviceInfo.label,
                            "capacity_kb": device.capacityInKB,
                            "capacity_gb": device.capacityInKB // (1024 * 1024)
                        })
            
            return {
                "vm_id": vm._GetMoId(),
                "name": vm.name,
                "status": vm.runtime.powerState.value,
                "cpu": vm.config.hardware.numCPU,
                "memory_mb": vm.config.hardware.memoryMB,
                "cpu_reservation": vm.resourceConfig.cpuAllocation.reservation if vm.resourceConfig else 0,
                "memory_reservation": vm.resourceConfig.memoryAllocation.reservation if vm.resourceConfig else 0,
                "ip_address": vm.guest.ipAddress if vm.guest else None,
                "host": vm.runtime.host.name if vm.runtime.host else None,
                "host_id": vm.runtime.host._GetMoId() if vm.runtime.host else None,
                "guest_full_name": vm.config.guestFullName,
                "guest_id": vm.config.guestId,
                "annotation": vm.config.annotation,
                "datastore": ",".join([ds.name for ds in vm.config.datastore]) if vm.config.datastore else None,
                "disks": disk_info,
                "num_ethernet_cards": len([d for d in vm.config.hardware.device if hasattr(d, 'macAddress')]),
                "created": vm.config.createDate.isoformat() if hasattr(vm.config, 'createDate') and vm.config.createDate else None,
            }
        except Exception as e:
            return {
                "vm_id": vm._GetMoId(),
                "name": vm.name,
                "status": vm.runtime.powerState.value,
                "cpu": vm.config.hardware.numCPU,
                "memory_mb": vm.config.hardware.memoryMB,
                "host": vm.runtime.host.name if vm.runtime.host else None,
                "guest_full_name": vm.config.guestFullName,
                "annotation": vm.config.annotation,
            }
    
    def get_vm_performance(self, vm_id: str) -> Optional[Dict[str, Any]]:
        vm = self._find_vm(vm_id)
        if not vm:
            return None
        
        try:
            stats = {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "network_usage": 0,
            }
            
            if vm.summary.runtime:
                stats["status"] = vm.summary.runtime.powerState.value
            
            if vm.summary.quickStats:
                qs = vm.summary.quickStats
                stats["cpu_usage"] = qs.cpuUsage if hasattr(qs, 'cpuUsage') and qs.cpuUsage else 0
                stats["memory_usage"] = qs.memoryUsage if hasattr(qs, 'memoryUsage') and qs.memoryUsage else 0
                stats["uptime_seconds"] = qs.uptimeSeconds if hasattr(qs, 'uptimeSeconds') and qs.uptimeSeconds else 0
            
            return stats
        except:
            return None
    
    @with_retry(max_attempts=3, delay=2.0)
    def power_on(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value != "poweredOn":
                task = vm.PowerOnVM_Task()
                self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to power on VM: {e}")
    
    @with_retry(max_attempts=3, delay=2.0)
    def power_off(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to power off VM: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def restart_vm(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
            task = vm.PowerOnVM_Task()
            self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to restart VM: {e}")
    
    @with_retry(max_attempts=3, delay=2.0)
    def suspend(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.SuspendVM_Task()
                self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to suspend VM: {e}")
    
    @with_retry(max_attempts=3, delay=2.0)
    def delete_vm(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
            task = vm.Destroy_Task()
            self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to delete VM: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def migrate_vm(
        self,
        vm_id: str,
        target_host_id: str = None,
        target_datastore_id: str = None,
        target_cluster_id: str = None,
        priority: str = "default"
    ) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            from pyVmomi import vim
            
            relocate_spec = vim.VirtualMachineRelocateSpec()
            
            if target_host_id:
                target_host = self._find_host_by_id(target_host_id)
                if not target_host:
                    raise VSphereOperationError(f"Target host {target_host_id} not found")
                relocate_spec.host = target_host
                relocate_spec.pool = target_host.parent.resourcePool
            
            if target_datastore_id:
                target_ds = self._find_datastore_by_id(target_datastore_id)
                if not target_ds:
                    raise VSphereOperationError(f"Target datastore {target_datastore_id} not found")
                relocate_spec.datastore = target_ds
            
            priority_map = {
                "low": vim.VirtualMachineMovePriority.lowPriority,
                "high": vim.VirtualMachineMovePriority.highPriority,
                "default": vim.VirtualMachineMovePriority.defaultPriority
            }
            move_priority = priority_map.get(priority, vim.VirtualMachineMovePriority.defaultPriority)
            
            task = vm.RelocateVM(spec=relocate_spec, priority=move_priority)
            self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to migrate VM: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def storage_vmotion(self, vm_id: str, target_datastore_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            from pyVmomi import vim
            
            target_ds = self._find_datastore_by_id(target_datastore_id)
            if not target_ds:
                raise VSphereOperationError(f"Target datastore {target_datastore_id} not found")
            
            relocate_spec = vim.VirtualMachineRelocateSpec()
            relocate_spec.datastore = target_ds
            
            if vm.runtime.host:
                relocate_spec.host = vm.runtime.host
                relocate_spec.pool = vm.runtime.host.parent.resourcePool
            
            task = vm.RelocateVM(spec=relocate_spec, priority=vim.VirtualMachineMovePriority.defaultPriority)
            self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to perform Storage vMotion: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def hot_resize(
        self,
        vm_id: str,
        cpu: int = None,
        memory_mb: int = None,
        disk_gb: int = None
    ) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            from pyVmomi import vim
            
            spec = vim.VirtualMachineConfigSpec()
            
            if cpu:
                spec.numCPUs = cpu
            
            if memory_mb:
                spec.memoryMB = memory_mb
            
            if disk_gb:
                for device in vm.config.hardware.device:
                    if hasattr(device, 'capacityInKB') and device.capacityInKB:
                        new_capacity_kb = disk_gb * 1024 * 1024
                        if device.capacityInKB < new_capacity_kb:
                            device.capacityInKB = new_capacity_kb
                            spec.deviceChange.append(
                                vim.VirtualDeviceConfigSpec(
                                    operation=vim.VirtualDeviceConfigSpecOperation.edit,
                                    device=device
                                )
                            )
            
            if spec.numCPUs or spec.memoryMB or spec.deviceChange:
                task = vm.Reconfigure(spec)
                self._wait_for_task(task)
            
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to hot-resize VM: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def clone_vm(
        self,
        vm_id: str,
        name: str,
        target_host_id: str = None,
        target_datastore_id: str = None,
        target_folder_id: str = None,
        linked_clone: bool = False,
        snapshot_id: str = None
    ) -> str:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            from pyVmomi import vim
            
            clone_spec = vim.VirtualMachineCloneSpec()
            clone_spec.powerOn = False
            clone_spec.template = False
            
            if linked_clone:
                clone_spec.location = vim.VirtualMachineRelocateSpec()
                
                if target_datastore_id:
                    target_ds = self._find_datastore_by_id(target_datastore_id)
                    if target_ds:
                        clone_spec.location.datastore = target_ds
                
                if target_host_id:
                    target_host = self._find_host_by_id(target_host_id)
                    if target_host:
                        clone_spec.location.host = target_host
                        clone_spec.location.pool = target_host.parent.resourcePool
                
                if snapshot_id:
                    snapshot = self._find_snapshot_by_id(vm, snapshot_id)
                    if snapshot:
                        clone_spec.snapshot = snapshot
                
                clone_spec.location.diskMoveType = "createNewChildDiskBacking"
            else:
                if target_datastore_id:
                    target_ds = self._find_datastore_by_id(target_datastore_id)
                    if target_ds:
                        if not clone_spec.location:
                            clone_spec.location = vim.VirtualMachineRelocateSpec()
                        clone_spec.location.datastore = target_ds
                
                if target_host_id:
                    target_host = self._find_host_by_id(target_host_id)
                    if target_host:
                        if not clone_spec.location:
                            clone_spec.location = vim.VirtualMachineRelocateSpec()
                        clone_spec.location.host = target_host
                        clone_spec.location.pool = target_host.parent.resourcePool
            
            vm_folder = None
            if target_folder_id:
                vm_folder = self._find_folder_by_id(target_folder_id)
            
            if not vm_folder:
                content = self._client.content
                vm_folder = content.rootFolder.childEntity[0].vmFolder
            
            task = vm.CloneVM(folder=vm_folder, name=name, spec=clone_spec)
            self._wait_for_task(task)
            
            cloned_vm = task.info.result
            return cloned_vm._GetMoId()
        except Exception as e:
            raise VSphereOperationError(f"Failed to clone VM: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def convert_to_template(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
            
            vm.MarkAsTemplate()
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to convert VM to template: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def convert_to_vm(self, template_id: str, target_host_id: str = None) -> bool:
        template = self._find_vm(template_id)
        if not template:
            raise VSphereOperationError(f"Template {template_id} not found")
        
        try:
            from pyVmomi import vim
            
            if target_host_id:
                target_host = self._find_host_by_id(target_host_id)
                if not target_host:
                    raise VSphereOperationError(f"Target host {target_host_id} not found")
                template.MarkAsVirtualMachine(pool=target_host.parent.resourcePool, host=target_host)
            else:
                template.MarkAsVirtualMachine()
            
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to convert template to VM: {e}")
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_snapshots(self, vm_id: str) -> List[Dict[str, Any]]:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            snapshot_info = vm.snapshot
            if not snapshot_info or not snapshot_info.rootSnapshotList:
                return []
            
            snapshots = []
            def traverse(snapshots_list, parent_path=""):
                for snap in snapshots_list:
                    snapshots.append({
                        "snapshot_id": snap.id,
                        "name": snap.name,
                        "description": snap.description,
                        "created": snap.createTime.isoformat() if snap.createTime else None,
                        "path": parent_path + "/" + snap.name if parent_path else snap.name,
                        "size_mb": 0,
                    })
                    if snap.childSnapshotList:
                        traverse(snap.childSnapshotList, snapshots[-1]["path"])
            
            traverse(snapshot_info.rootSnapshotList)
            return snapshots
        except Exception as e:
            logger.error(f"Error getting snapshots: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=5.0)
    def create_snapshot(self, vm_id: str, name: str, description: str = "", memory: bool = False) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            task = vm.CreateSnapshot_Task(name, description, memory)
            self._wait_for_task(task)
            return True
        except Exception as e:
            raise VSphereOperationError(f"Failed to create snapshot: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            snapshot_info = vm.snapshot
            if snapshot_info and snapshot_info.rootSnapshotList:
                def find_snap(snapshots, snap_id):
                    for snap in snapshots:
                        if str(snap.id) == str(snapshot_id):
                            return snap
                        if snap.childSnapshotList:
                            result = find_snap(snap.childSnapshotList, snap_id)
                            if result:
                                return result
                    return None
                
                target_snap = find_snap(snapshot_info.rootSnapshotList, snapshot_id)
                if target_snap:
                    task = target_snap.RevertToSnapshot_Task()
                    self._wait_for_task(task)
                    return True
            raise VSphereOperationError(f"Snapshot {snapshot_id} not found")
        except Exception as e:
            raise VSphereOperationError(f"Failed to revert snapshot: {e}")
    
    @with_retry(max_attempts=3, delay=5.0)
    def delete_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            raise VSphereOperationError(f"VM {vm_id} not found")
        
        try:
            snapshot_info = vm.snapshot
            if snapshot_info and snapshot_info.rootSnapshotList:
                def find_snap(snapshots, snap_id):
                    for snap in snapshots:
                        if str(snap.id) == str(snapshot_id):
                            return snap
                        if snap.childSnapshotList:
                            result = find_snap(snap.childSnapshotList, snap_id)
                            if result:
                                return result
                    return None
                
                target_snap = find_snap(snapshot_info.rootSnapshotList, snapshot_id)
                if target_snap:
                    task = target_snap.RemoveSnapshot_Task(removeChildren=False)
                    self._wait_for_task(task)
                    return True
            raise VSphereOperationError(f"Snapshot {snapshot_id} not found")
        except Exception as e:
            raise VSphereOperationError(f"Failed to delete snapshot: {e}")
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_hosts(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            hosts = content.rootFolder.childEntity[0].hostFolder.childEntity
            
            result = []
            for host in hosts:
                try:
                    result.append({
                        "host_id": host._GetMoId(),
                        "name": host.name,
                        "status": host.runtime.connectionState.value,
                        "maintenance_mode": host.runtime.inMaintenanceMode if hasattr(host.runtime, 'inMaintenanceMode') else False,
                    })
                except Exception as e:
                    logger.warning(f"Error getting host info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting hosts: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_host_by_id(self, host_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            hosts = content.rootFolder.childEntity[0].hostFolder.childEntity
            
            for host in hosts:
                if host._GetMoId() == host_id:
                    return {
                        "host_id": host._GetMoId(),
                        "name": host.name,
                        "status": host.runtime.connectionState.value,
                        "maintenance_mode": host.runtime.inMaintenanceMode if hasattr(host.runtime, 'inMaintenanceMode') else False,
                        "cpu_cores": host.hardware.cpu.numCpuCores,
                        "cpu_mhz": host.hardware.cpu.hz,
                        "memory_bytes": host.hardware.memorySize,
                        "cpu_usage": 0,
                        "memory_usage": 0,
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting host: {e}")
            return None
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_clusters(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            clusters = content.rootFolder.childEntity[0].hostFolder.childEntity
            
            result = []
            for cluster in clusters:
                try:
                    if hasattr(cluster, 'resourcePool'):
                        result.append({
                            "cluster_id": cluster._GetMoId(),
                            "name": cluster.name,
                            "host_count": len(cluster.host) if hasattr(cluster, 'host') else 0,
                            "total_cpu_cores": cluster.summary.totalCpu if hasattr(cluster, 'summary') else 0,
                            "total_memory_gb": cluster.summary.totalMemory / (1024**3) if hasattr(cluster, 'summary') and hasattr(cluster.summary, 'totalMemory') else 0,
                        })
                except Exception as e:
                    logger.warning(f"Error getting cluster info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting clusters: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_datastores(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            datastores = content.rootFolder.childEntity[0].datastoreFolder.childEntity
            
            result = []
            for ds in datastores:
                try:
                    result.append({
                        "datastore_id": ds._GetMoId(),
                        "name": ds.name,
                        "type": ds.info.type if hasattr(ds, 'info') else "Unknown",
                        "capacity_gb": ds.info.maxCapacityKB // 1024 if hasattr(ds, 'info') and hasattr(ds.info, 'maxCapacityKB') else 0,
                        "free_gb": ds.info.freeSpaceKB // 1024 if hasattr(ds, 'info') and hasattr(ds.info, 'freeSpaceKB') else 0,
                        "used_percent": 0,
                    })
                except Exception as e:
                    logger.warning(f"Error getting datastore info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting datastores: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_networks(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            networks = content.rootFolder.childEntity[0].networkFolder.childEntity
            
            result = []
            for network in networks:
                try:
                    result.append({
                        "network_id": network._GetMoId(),
                        "name": network.name,
                        "type": "DistributedPortGroup" if hasattr(network, 'config') and hasattr(network.config, 'type') and network.config.type == "distributedVirtualPortGroup" else "Standard",
                    })
                except Exception as e:
                    logger.warning(f"Error getting network info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting networks: {e}")
            return []
    
    @with_retry(max_attempts=3, delay=1.0)
    def get_datacenters(self) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            content = self._client.content
            datacenters = content.rootFolder.childEntity
            
            result = []
            for dc in datacenters:
                try:
                    result.append({
                        "dc_id": dc._GetMoId(),
                        "name": dc.name,
                    })
                except Exception as e:
                    logger.warning(f"Error getting datacenter info: {e}")
            return result
        except Exception as e:
            logger.error(f"Error getting datacenters: {e}")
            return []
    
    def get_overview(self) -> Dict[str, Any]:
        vms = self.get_vms()
        hosts = self.get_hosts()
        datastores = self.get_datastores()
        
        powered_on = sum(1 for vm in vms if vm.get("status") == "poweredOn")
        powered_off = sum(1 for vm in vms if vm.get("status") == "poweredOff")
        
        total_memory_gb = sum((host.get("memory_bytes", 0) or 0) for host in hosts) / (1024**3)
        
        total_storage_tb = sum((ds.get("capacity_gb", 0) or 0) for ds in datastores) / 1024
        used_storage_tb = sum(((ds.get("capacity_gb", 0) or 0) - (ds.get("free_gb", 0) or 0)) for ds in datastores) / 1024
        
        return {
            "total_hosts": len(hosts),
            "total_vms": len(vms),
            "vm_by_status": {
                "poweredOn": powered_on,
                "poweredOff": powered_off
            },
            "total_memory_gb": round(total_memory_gb, 2),
            "total_storage_tb": round(total_storage_tb, 2),
            "used_storage_tb": round(used_storage_tb, 2),
            "used_storage_percent": round((used_storage_tb / total_storage_tb * 100) if total_storage_tb > 0 else 0, 1),
            "datastore_count": len(datastores),
        }


_vsphere_client: Optional[VSphereClient] = None


def get_vsphere_client() -> VSphereClient:
    global _vsphere_client
    if _vsphere_client is None:
        _vsphere_client = VSphereClient()
    return _vsphere_client


def reset_vsphere_client():
    global _vsphere_client
    if _vsphere_client:
        _vsphere_client.disconnect()
    _vsphere_client = VSphereClient()
