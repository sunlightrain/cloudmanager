import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.vsphere.pool import get_connection_pool, ConnectionConfig
from app.core.vsphere.exceptions import (
    VSphereConnectionError,
    VSphereObjectNotFoundError,
    VSphereOperationError,
    VSphereTimeoutError,
)

logger = logging.getLogger(__name__)


class VSphereClient:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 443,
        datacenter: Optional[str] = None
    ):
        self.config = ConnectionConfig(
            host=host,
            user=user,
            password=password,
            port=port
        )
        self._pool = get_connection_pool()
        self._connection = None
        self._datacenter = datacenter
        self._si = None
        self._content = None
        self._root_folder = None
        self._view_manager = None

    def __enter__(self):
        self._connection = self._pool.get_connection(self.config)
        self._si = self._connection.si
        self._content = self._si.RetrieveContent()
        self._root_folder = self._content.rootFolder
        self._view_manager = self._content.viewManager
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            self._pool.release_connection(self._connection)
            self._connection = None

    def _get_dc(self, dc_name: Optional[str] = None):
        if dc_name:
            return self.get_obj(self._content.rootFolder, [vim.Datacenter], dc_name)
        
        if self._datacenter:
            return self.get_obj(self._content.rootFolder, [vim.Datacenter], self._datacenter)
        
        dcs = self.get_all_objs([vim.Datacenter])
        if dcs:
            return list(dcs.values())[0]
        return None

    def get_obj(self, root_folder, vim_types: List, name: str) -> Optional[Any]:
        container = root_folder
        container_view = self._view_manager.CreateContainerView(
            container=container,
            type=vim_types,
            recursive=True
        )
        
        try:
            for obj in container_view.view:
                if obj.name == name:
                    return obj
        finally:
            container_view.Destroy()
        
        return None

    def get_all_objs(self, vim_types: List, begin_entity: Optional[Any] = None) -> Dict[str, Any]:
        if begin_entity is None:
            begin_entity = self._root_folder
        
        container_view = self._view_manager.CreateContainerView(
            container=begin_entity,
            type=vim_types,
            recursive=True
        )
        
        try:
            return {obj.name: obj for obj in container_view.view}
        finally:
            container_view.Destroy()

    def get_all_datacenters(self) -> List[Any]:
        return list(self.get_all_objs([vim.Datacenter]).values())

    def get_datacenter(self, name: str) -> Optional[Any]:
        return self.get_obj(self._root_folder, [vim.Datacenter], name)

    def get_all_clusters(self, dc_name: Optional[str] = None) -> List[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return []
        return list(self.get_all_objs([vim.ClusterComputeResource], dc).values())

    def get_cluster(self, name: str, dc_name: Optional[str] = None) -> Optional[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return None
        return self.get_obj(dc, [vim.ClusterComputeResource], name)

    def get_cluster_hosts(self, cluster: Any) -> List[Any]:
        return list(cluster.host) if hasattr(cluster, 'host') else []

    def get_cluster_resource_summary(self, cluster: Any) -> Dict[str, Any]:
        summary = cluster.summary
        if not summary:
            return {}
        
        cpu_total = summary.totalCpu
        cpu_used = cpu_total - summary.effectiveCpu if summary.effectiveCpu else 0
        mem_total = summary.totalMemory
        mem_used = mem_total - summary.effectiveMemory * 1024 * 1024 * 1024 if summary.effectiveMemory else 0
        
        return {
            "cluster_id": cluster._GetMoId(),
            "name": cluster.name,
            "cpu_total_mhz": cpu_total,
            "cpu_used_mhz": cpu_used,
            "cpu_free_mhz": summary.effectiveCpu,
            "cpu_usage_percent": round(cpu_used / cpu_total * 100, 2) if cpu_total > 0 else 0,
            "mem_total_gb": round(mem_total / (1024**3), 2),
            "mem_used_gb": round(mem_used / (1024**3), 2),
            "mem_free_gb": round(summary.effectiveMemory * 1024, 2) if summary.effectiveMemory else 0,
            "mem_usage_percent": round(mem_used / mem_total * 100, 2) if mem_total > 0 else 0,
            "host_count": len(cluster.host) if hasattr(cluster, 'host') else 0,
            "drs_enabled": summary.drsConfig.enabled if hasattr(summary, 'drsConfig') and summary.drsConfig else False,
            "drs_runtime_info": str(summary.drsConfig) if hasattr(summary, 'drsConfig') and summary.drsConfig else None,
            "ha_enabled": summary.haConfig.enabled if hasattr(summary, 'haConfig') and summary.haConfig else False,
        }

    def get_all_hosts(self, dc_name: Optional[str] = None) -> List[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return []
        return list(self.get_all_objs([vim.HostSystem], dc).values())

    def get_host(self, name: str, dc_name: Optional[str] = None) -> Optional[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return None
        return self.get_obj(dc, [vim.HostSystem], name)

    def get_host_by_id(self, host_id: str, dc_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        hosts = self.get_all_hosts(dc_name)
        for host in hosts:
            if host._GetMoId() == host_id:
                return self._format_host(host)
        return None

    def _format_host(self, host: Any) -> Dict[str, Any]:
        hardware = host.hardware
        summary = host.summary
        
        cpu_info = {}
        if hardware and hardware.cpuPkg:
            cpu_info = {
                "model": hardware.cpuPkg[0].name if hardware.cpuPkg else "Unknown",
                "cores": hardware.cpuInfo.numCpuCores if hardware.cpuInfo else 0,
                "threads": hardware.cpuInfo.numCpuThreads if hardware.cpuInfo else 0,
                "packages": hardware.cpuInfo.numCpuPackages if hardware.cpuInfo else 0,
            }
        
        memory_info = {}
        if hardware:
            memory_info = {
                "total_bytes": hardware.memorySize,
                "total_gb": round(hardware.memorySize / (1024**3), 2),
            }
        
        runtime = host.runtime if host.runtime else {}
        quick_stats = summary.quickStats if summary and hasattr(summary, 'quickStats') else {}
        
        storage_info = []
        if host.datastore:
            for ds in host.datastore:
                try:
                    storage_info.append({
                        "name": ds.name,
                        "capacity_gb": round(ds.summary.capacity / (1024**3), 2) if ds.summary else 0,
                        "free_gb": round(ds.summary.freeSpace / (1024**3), 2) if ds.summary else 0,
                    })
                except:
                    pass
        
        return {
            "host_id": host._GetMoId(),
            "name": host.name,
            "status": str(runtime.get('connectionState', 'unknown')) if isinstance(runtime, dict) else str(runtime.connectionState.value if hasattr(runtime, 'connectionState') else 'unknown'),
            "power_state": str(runtime.get('powerState', 'unknown')) if isinstance(runtime, dict) else str(runtime.powerState.value if hasattr(runtime, 'powerState') else 'unknown'),
            "maintenance_mode": runtime.inMaintenanceMode if hasattr(runtime, 'inMaintenanceMode') else False,
            "cpu_info": cpu_info,
            "memory_info": memory_info,
            "storage": storage_info,
            "cpu_usage_percent": quick_stats.overallCpuUsage if hasattr(quick_stats, 'overallCpuUsage') else 0,
            "memory_usage_gb": quick_stats.overallMemoryUsage if hasattr(quick_stats, 'overallMemoryUsage') else 0,
        }

    def get_all_vms(self, dc_name: Optional[str] = None) -> List[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return []
        return list(self.get_all_objs([vim.VirtualMachine], dc.vmFolder).values())

    def get_vm(self, name: str, dc_name: Optional[str] = None) -> Optional[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return None
        return self.get_obj(dc.vmFolder, [vim.VirtualMachine], name)

    def get_vm_by_id(self, vm_id: str, dc_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        vms = self.get_all_vms(dc_name)
        for vm in vms:
            if vm._GetMoId() == vm_id:
                return self._format_vm(vm)
        return None

    def get_vm_by_uuid(self, uuid: str) -> Optional[Any]:
        try:
            search_index = self._si.content.searchIndex
            return search_index.FindByUuid(None, uuid, True, True)
        except:
            return None

    def _format_vm(self, vm: Any) -> Dict[str, Any]:
        summary = vm.summary
        config = summary.config if summary else None
        runtime = summary.runtime if summary else None
        guest = summary.guest if summary else None
        
        if not config:
            return {"vm_id": vm._GetMoId(), "name": vm.name}
        
        disks = []
        if hasattr(config, 'device') and config.device:
            for device in config.device:
                if hasattr(device, 'capacityInKB'):
                    disks.append({
                        "label": device.deviceInfo.label if hasattr(device.deviceInfo, 'label') else "Unknown",
                        "capacity_kb": device.capacityInKB,
                        "capacity_gb": round(device.capacityInKB / (1024 * 1024), 2),
                    })
        
        networks = []
        if hasattr(config, 'device') and config.device:
            for device in config.device:
                if hasattr(device, 'macAddress'):
                    networks.append({
                        "label": device.deviceInfo.label if hasattr(device.deviceInfo, 'label') else "Unknown",
                        "mac_address": device.macAddress,
                        "address_type": device.addressType if hasattr(device, 'addressType') else "generated",
                    })
        
        return {
            "vm_id": vm._GetMoId(),
            "name": config.name,
            "uuid": config.uuid,
            "status": str(runtime.powerState.value) if runtime and hasattr(runtime, 'powerState') else "unknown",
            "cpu": config.numCpu,
            "memory_mb": config.memorySizeMB,
            "guest_full_name": config.guestFullName,
            "guest_id": config.guestId,
            "ip_address": guest.ipAddress if guest and hasattr(guest, 'ipAddress') else None,
            "host_name": guest.hostName if guest and hasattr(guest, 'hostName') else None,
            "host_id": runtime.host._GetMoId() if runtime and hasattr(runtime, 'host') and runtime.host else None,
            "tools_status": str(guest.toolsStatus.value) if guest and hasattr(guest, 'toolsStatus') else "unknown",
            "tools_version": guest.toolsVersion if guest and hasattr(guest, 'toolsVersion') else 0,
            "annotation": config.annotation if hasattr(config, 'annotation') else None,
            "disks": disks,
            "networks": networks,
            "datastore": ",".join([ds.name for ds in config.datastore]) if hasattr(config, 'datastore') and config.datastore else None,
        }

    def get_all_datastores(self, dc_name: Optional[str] = None) -> List[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return []
        return list(self.get_all_objs([vim.Datastore], dc).values())

    def get_datastore(self, name: str, dc_name: Optional[str] = None) -> Optional[Any]:
        dc = self._get_dc(dc_name)
        if not dc:
            return None
        return self.get_obj(dc, [vim.Datastore], name)

    def get_datastore_summary(self, datastore: Any) -> Dict[str, Any]:
        summary = datastore.summary
        if not summary:
            return {"name": datastore.name}
        
        return {
            "datastore_id": datastore._GetMoId(),
            "name": summary.name,
            "type": summary.type,
            "capacity_gb": round(summary.capacity / (1024**3), 2),
            "free_gb": round(summary.freeSpace / (1024**3), 2),
            "used_gb": round((summary.capacity - summary.freeSpace) / (1024**3), 2),
            "usage_percent": round((summary.capacity - summary.freeSpace) / summary.capacity * 100, 2) if summary.capacity > 0 else 0,
            "vm_count": summary.vmCount,
            "accessible": summary.accessible,
        }

    def get_all_networks(self, dc_name: Optional[str] = None) -> List[Dict[str, Any]]:
        dc = self._get_dc(dc_name)
        if not dc:
            return []
        
        networks = []
        
        for name, network in self.get_all_objs([vim.Network], dc).items():
            networks.append({
                "network_id": network._GetMoId(),
                "name": name,
                "type": "standard",
            })
        
        for name, dvs in self.get_all_objs([vim.dvs.VmwareDistributedVirtualSwitch], dc).items():
            networks.append({
                "network_id": dvs._GetMoId(),
                "name": name,
                "type": "distributed",
                "port_group_count": len(dvs.portgroup) if hasattr(dvs, 'portgroup') else 0,
            })
        
        for name, pg in self.get_all_objs([vim.DistributedVirtualPortgroup], dc).items():
            networks.append({
                "network_id": pg._GetMoId(),
                "name": name,
                "type": "portgroup",
                "vlan_id": pg.config.defaultPortConfig.vlan.vlanId if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') and hasattr(pg.config.defaultPortConfig, 'vlan') and hasattr(pg.config.defaultPortConfig.vlan, 'vlanId') else 0,
            })
        
        return networks

    def get_vm_snapshots(self, vm: Any) -> List[Dict[str, Any]]:
        if not hasattr(vm, 'snapshot') or not vm.snapshot or not vm.snapshot.rootSnapshotList:
            return []
        
        snapshots = []
        
        def traverse(snap_list: List, parent_path: str = ""):
            for snap in snap_list:
                path = f"{parent_path}/{snap.name}" if parent_path else snap.name
                snapshots.append({
                    "snapshot_id": snap.id,
                    "name": snap.name,
                    "description": snap.description,
                    "created": snap.createTime.isoformat() if snap.createTime else None,
                    "state": str(snap.state.value) if hasattr(snap.state, 'value') else "unknown",
                    "path": path,
                })
                if hasattr(snap, 'childSnapshotList') and snap.childSnapshotList:
                    traverse(snap.childSnapshotList, path)
        
        traverse(vm.snapshot.rootSnapshotList)
        return snapshots

    def create_snapshot(self, vm: Any, name: str, description: str = "", memory: bool = False, quiesce: bool = False) -> str:
        task = vm.CreateSnapshot_Task(name=name, description=description, memory=memory, quiesce=quiesce)
        self._wait_for_task(task)
        return name

    def remove_snapshot(self, vm: Any, snapshot_id: int, remove_children: bool = False) -> bool:
        snapshots = self.get_vm_snapshots(vm)
        for snap in snapshots:
            if snap['snapshot_id'] == snapshot_id:
                root_snap = self._find_snapshot_by_id(vm, snapshot_id)
                if root_snap:
                    task = root_snap.RemoveSnapshot_Task(removeChildren=remove_children)
                    self._wait_for_task(task)
                    return True
        return False

    def _find_snapshot_by_id(self, vm: Any, snapshot_id: int) -> Optional[Any]:
        if not hasattr(vm, 'snapshot') or not vm.snapshot or not vm.snapshot.rootSnapshotList:
            return None
        
        def find(snap_list: List):
            for snap in snap_list:
                if snap.id == snapshot_id:
                    return snap.snapshot
                if hasattr(snap, 'childSnapshotList') and snap.childSnapshotList:
                    result = find(snap.childSnapshotList)
                    if result:
                        return result
            return None
        
        return find(vm.snapshot.rootSnapshotList)

    def revert_to_snapshot(self, vm: Any, snapshot_id: int) -> bool:
        root_snap = self._find_snapshot_by_id(vm, snapshot_id)
        if root_snap:
            task = root_snap.RevertToSnapshotTask()
            self._wait_for_task(task)
            return True
        return False

    def power_on_vm(self, vm: Any) -> bool:
        if hasattr(vm, 'runtime') and hasattr(vm.runtime, 'powerState'):
            if vm.runtime.powerState.value != "poweredOn":
                task = vm.PowerOnVM_Task()
                self._wait_for_task(task)
        return True

    def power_off_vm(self, vm: Any) -> bool:
        if hasattr(vm, 'runtime') and hasattr(vm.runtime, 'powerState'):
            if vm.runtime.powerState.value == "poweredOn":
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
        return True

    def _wait_for_task(self, task: Any, timeout: int = 600) -> Any:
        import time
        start_time = time.time()
        
        while True:
            if task.info.state == vim.TaskInfo.State.success:
                return task.info.result
            elif task.info.state == vim.TaskInfo.State.error:
                error_msg = task.info.error.localizedMessage if hasattr(task.info.error, 'localizedMessage') else str(task.info.error)
                raise VSphereOperationError(f"Task failed: {error_msg}")
            
            if time.time() - start_time > timeout:
                raise VSphereTimeoutError(f"Task timeout after {timeout} seconds")
            
            time.sleep(1)


def get_vsphere_client(host: str, user: str, password: str, port: int = 443, datacenter: Optional[str] = None) -> VSphereClient:
    return VSphereClient(host=host, user=user, password=password, port=port, datacenter=datacenter)


import vim
