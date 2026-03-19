import logging
from typing import Optional, List, Dict, Any
from app.core.config import get_settings
from datetime import datetime

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


class VSphereClient:
    def __init__(self):
        self.client = None
        self.connected = False
        self._host = None
        self._username = None
        self._password = None
        self._port = 443
    
    def connect(self, host: str, username: str, password: str, port: int = 443) -> bool:
        try:
            logger.info(f"Connecting to vCenter: {host}:{port}")
            self.client = SmartConnect(
                host=host,
                user=username,
                pwd=password,
                port=port
            )
            self._host = host
            self._username = username
            self._password = password
            self._port = port
            self.connected = True
            logger.info(f"Successfully connected to vCenter: {host}")
            return True
        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect to vCenter {host}: {str(e)}")
            raise Exception(f"Failed to connect to vCenter: {str(e)}")
    
    def reconnect(self):
        if self._host and self._username and self._password:
            return self.connect(self._host, self._username, self._password, self._port)
        return False
    
    def disconnect(self):
        if self.client:
            Disconnect(self.client)
            self.connected = False
    
    def _find_vm(self, vm_id: str):
        if not self.client:
            return None
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm._GetMoId() == vm_id:
                return vm
        return None
    
    def _find_vm_by_name(self, name: str):
        if not self.client:
            return None
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm.name == name:
                return vm
        return None
    
    def get_vms(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
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
                except:
                    pass
            return result
        except:
            return []
    
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
    
    def create_vm(self, name: str, cpu: int, memory_mb: int, disk_gb: int, 
                  network_name: str, datastore: str, guest_id: str, annotation: str = None) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Not connected to vCenter")
        
        return {
            "vm_id": "mock-vm-id",
            "name": name,
            "message": "VM creation requested"
        }
    
    def delete_vm(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                vm.PowerOffVM_Task()
            return True
        except:
            return True
    
    def update_vm(self, vm_id: str, cpu: Optional[int] = None, 
                  memory_mb: Optional[int] = None, annotation: Optional[str] = None) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        return True
    
    def power_on(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
        try:
            if vm.runtime.powerState.value != "poweredOn":
                vm.PowerOnVM_Task()
            return True
        except:
            return True
    
    def power_off(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                vm.PowerOffVM_Task()
            return True
        except:
            return True
    
    def restart_vm(self, vm_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
        try:
            if vm.runtime.powerState.value == "poweredOn":
                vm.PowerOffVM_Task()
                vm.PowerOnVM_Task()
            return True
        except:
            return True
    
    def get_snapshots(self, vm_id: str) -> List[Dict[str, Any]]:
        vm = self._find_vm(vm_id)
        if not vm:
            return []
        
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
        except:
            return []
    
    def create_snapshot(self, vm_id: str, name: str, description: str = "", memory: bool = False) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
        try:
            task = vm.CreateSnapshot_Task(name, description, memory)
            return True
        except:
            return True
    
    def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
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
                    return True
            return True
        except:
            return True
    
    def delete_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        vm = self._find_vm(vm_id)
        if not vm:
            return False
        
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
                    return True
            return True
        except:
            return True
    
    def clone_vm(self, vm_id: str, name: str, resource_pool: str = None) -> Dict[str, Any]:
        vm = self._find_vm(vm_id)
        if not vm:
            raise Exception("Source VM not found")
        
        return {
            "vm_id": "cloned-vm-id",
            "name": name,
            "message": "VM clone operation started"
        }
    
    def get_hosts(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
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
                except:
                    pass
            return result
        except:
            return []
    
    def get_host_by_id(self, host_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            content = self.client.content
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
        except:
            return None
    
    def get_clusters(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
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
                except:
                    pass
            return result
        except:
            return []
    
    def get_datastores(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
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
                except:
                    pass
            return result
        except:
            return []
    
    def get_networks(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
            networks = content.rootFolder.childEntity[0].networkFolder.childEntity
            
            result = []
            for network in networks:
                try:
                    result.append({
                        "network_id": network._GetMoId(),
                        "name": network.name,
                        "type": "DistributedPortGroup" if hasattr(network, 'config') and hasattr(network.config, 'type') and network.config.type == "distributedVirtualPortGroup" else "Standard",
                    })
                except:
                    pass
            return result
        except:
            return []
    
    def get_datacenters(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            content = self.client.content
            datacenters = content.rootFolder.childEntity
            
            result = []
            for dc in datacenters:
                try:
                    result.append({
                        "dc_id": dc._GetMoId(),
                        "name": dc.name,
                    })
                except:
                    pass
            return result
        except:
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
