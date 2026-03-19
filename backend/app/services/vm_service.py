import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.vsphere.client import get_vsphere_client
from app.core.vsphere.exceptions import VSphereOperationError
from app.tasks.vm_tasks import create_vm_task, vm_power_operation_task, delete_vm_task, clone_vm_task, resize_vm_resources_task

logger = logging.getLogger(__name__)


class VMService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def list_vms(self, name: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            vms = client.get_all_vms(self.datacenter)
            vm_list = []
            
            for vm in vms:
                try:
                    vm_data = client._format_vm(vm)
                    vm_list.append(vm_data)
                except Exception as e:
                    logger.error(f"Error formatting VM {vm.name}: {e}")
            
            if name:
                vm_list = [vm for vm in vm_list if name.lower() in vm.get("name", "").lower()]
            if status:
                vm_list = [vm for vm in vm_list if vm.get("status") == status]
            
            return vm_list

    def get_vm(self, vm_id: str) -> Optional[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            return client.get_vm_by_id(vm_id)

    def get_vm_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            vm = client.get_vm(name, self.datacenter)
            if vm:
                return client._format_vm(vm)
            return None

    def create_vm_async(
        self,
        name: str,
        cpu: int,
        memory_mb: int,
        disk_gb: int,
        guest_id: str = "otherLinuxGuest",
        datacenter: Optional[str] = None,
        cluster: Optional[str] = None,
        resource_pool: Optional[str] = None,
        annotation: str = "",
        networks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        vm_config = {
            "name": name,
            "cpu": cpu,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb,
            "guest_id": guest_id,
            "annotation": annotation,
            "networks": networks or []
        }
        
        dc = datacenter or self.datacenter or "Datacenter"
        cluster = cluster or "Cluster"
        
        task = create_vm_task.apply_async(
            kwargs={
                "vcenter_config": self.vcenter_config,
                "vm_config": vm_config,
                "datacenter": dc,
                "cluster": cluster,
                "resource_pool": resource_pool
            }
        )
        
        return task.id

    def power_operation(self, vm_id: str, operation: str) -> Dict[str, Any]:
        if operation not in ["start", "stop", "restart", "suspend", "resume"]:
            raise VSphereOperationError(f"Invalid operation: {operation}")
        
        task = vm_power_operation_task.apply_async(
            kwargs={
                "vcenter_config": self.vcenter_config,
                "vm_id": vm_id,
                "operation": operation,
                "datacenter": self.datacenter
            }
        )
        
        return {
            "task_id": task.id,
            "operation": operation,
            "vm_id": vm_id
        }

    def delete_vm_async(self, vm_id: str) -> str:
        task = delete_vm_task.apply_async(
            kwargs={
                "vcenter_config": self.vcenter_config,
                "vm_id": vm_id,
                "datacenter": self.datacenter
            }
        )
        return task.id

    def clone_vm_async(
        self,
        source_vm_id: str,
        clone_name: str,
        datacenter: Optional[str] = None,
        cluster: Optional[str] = None,
        resource_pool: Optional[str] = None
    ) -> str:
        dc = datacenter or self.datacenter or "Datacenter"
        cluster = cluster or "Cluster"
        
        task = clone_vm_task.apply_async(
            kwargs={
                "vcenter_config": self.vcenter_config,
                "source_vm_id": source_vm_id,
                "clone_name": clone_name,
                "datacenter": dc,
                "cluster": cluster,
                "resource_pool": resource_pool
            }
        )
        
        return task.id

    def resize_resources_async(
        self,
        vm_id: str,
        cpu: Optional[int] = None,
        memory_mb: Optional[int] = None
    ) -> str:
        task = resize_vm_resources_task.apply_async(
            kwargs={
                "vcenter_config": self.vcenter_config,
                "vm_id": vm_id,
                "cpu": cpu,
                "memory_mb": memory_mb,
                "datacenter": self.datacenter
            }
        )
        return task.id

    def get_snapshots(self, vm_id: str) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            vms = client.get_all_vms(self.datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            return client.get_vm_snapshots(vm)

    def get_vm_performance(self, vm_id: str) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            vms = client.get_all_vms(self.datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            quick_stats = vm.summary.quickStats if hasattr(vm, 'summary') and vm.summary and hasattr(vm.summary, 'quickStats') else {}
            
            return {
                "cpu_usage": quick_stats.overallCpuUsage if hasattr(quick_stats, 'overallCpuUsage') else 0,
                "memory_usage": quick_stats.overallMemoryUsage if hasattr(quick_stats, 'overallMemoryUsage') else 0,
                "uptime_seconds": quick_stats.uptimeSeconds if hasattr(quick_stats, 'uptimeSeconds') else 0,
                "guest_memory_usage": quick_stats.guestMemoryUsage if hasattr(quick_stats, 'guestMemoryUsage') else 0,
                "host_memory_usage": quick_stats.hostMemoryUsage if hasattr(quick_stats, 'hostMemoryUsage') else 0,
            }

    def get_available_resources(self, cluster: Optional[str] = None) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            if cluster:
                cluster_obj = client.get_cluster(cluster, self.datacenter)
                if not cluster_obj:
                    raise VSphereOperationError(f"Cluster {cluster} not found")
                clusters = [cluster_obj]
            else:
                clusters = client.get_all_clusters(self.datacenter)
            
            total_cpu_mhz = 0
            total_memory_gb = 0
            available_cpu_mhz = 0
            available_memory_gb = 0
            
            for c in clusters:
                summary = c.summary
                if summary:
                    total_cpu_mhz += summary.totalCpu
                    total_memory_gb += summary.totalMemory / (1024**3)
                    available_cpu_mhz += summary.effectiveCpu
                    available_memory_gb += summary.effectiveMemory
            
            return {
                "cpu": {
                    "total_mhz": total_cpu_mhz,
                    "available_mhz": available_cpu_mhz,
                    "used_mhz": total_cpu_mhz - available_cpu_mhz,
                    "usage_percent": round((total_cpu_mhz - available_cpu_mhz) / total_cpu_mhz * 100, 2) if total_cpu_mhz > 0 else 0
                },
                "memory": {
                    "total_gb": round(total_memory_gb, 2),
                    "available_gb": round(available_memory_gb, 2),
                    "used_gb": round(total_memory_gb - available_memory_gb, 2),
                    "usage_percent": round((total_memory_gb - available_memory_gb) / total_memory_gb * 100, 2) if total_memory_gb > 0 else 0
                }
            }
