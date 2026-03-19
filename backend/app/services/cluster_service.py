import logging
from typing import Optional, Dict, Any, List

from app.core.vsphere.client import get_vsphere_client
from app.core.vsphere.exceptions import VSphereOperationError

logger = logging.getLogger(__name__)


class ClusterService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def list_clusters(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            clusters = client.get_all_clusters(self.datacenter)
            result = []
            
            for cluster in clusters:
                try:
                    summary = client.get_cluster_resource_summary(cluster)
                    result.append(summary)
                except Exception as e:
                    logger.error(f"Error formatting cluster {cluster.name}: {e}")
            
            return result

    def get_cluster(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            clusters = client.get_all_clusters(self.datacenter)
            
            for cluster in clusters:
                if cluster._GetMoId() == cluster_id:
                    return client.get_cluster_resource_summary(cluster)
            
            return None

    def get_cluster_hosts(self, cluster_id: str) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            clusters = client.get_all_clusters(self.datacenter)
            
            for cluster in clusters:
                if cluster._GetMoId() == cluster_id:
                    hosts = client.get_cluster_hosts(cluster)
                    return [client._format_host(h) for h in hosts]
            
            return []

    def get_ha_config(self, cluster_id: str) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            clusters = client.get_all_clusters(self.datacenter)
            
            for cluster in clusters:
                if cluster._GetMoId() == cluster_id:
                    if not hasattr(cluster, 'configuration') or not cluster.configuration:
                        return {"enabled": False, "error": "HA config not available"}
                    
                    ha_config = cluster.configuration.dasConfig
                    
                    return {
                        "enabled": ha_config.enabled if hasattr(ha_config, 'enabled') else False,
                        "admission_control": {
                            "enabled": ha_config.admissionControlEnabled if hasattr(ha_config, 'admissionControlEnabled') else False,
                            "policy": str(ha_config.admissionControlPolicy.__class__.__name__) if hasattr(ha_config, 'admissionControlPolicy') else "None"
                        },
                        "failover_level": ha_config.failoverLevel if hasattr(ha_config, 'failoverLevel') else 1,
                        "default_vm_timeout": ha_config.defaultVmSettings.restartPriority if hasattr(ha_config, 'defaultVmSettings') and hasattr(ha_config.defaultVmSettings, 'restartPriority') else None,
                        "isolation_response": ha_config.defaultVmSettings.isolationResponse if hasattr(ha_config, 'defaultVmSettings') and hasattr(ha_config.defaultVmSettings, 'isolationResponse') else None,
                    }
            
            return {}

    def get_drs_config(self, cluster_id: str) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            clusters = client.get_all_clusters(self.datacenter)
            
            for cluster in clusters:
                if cluster._GetMoId() == cluster_id:
                    if not hasattr(cluster, 'configuration') or not cluster.configuration:
                        return {"enabled": False, "error": "DRS config not available"}
                    
                    DrsConfig = cluster.configuration.drsConfig
                    
                    return {
                        "enabled": DrsConfig.enabled if hasattr(DrsConfig, 'enabled') else False,
                        "automation_level": str(DrsConfig.defaultVmBehavior) if hasattr(DrsConfig, 'defaultVmBehavior') else "manual",
                        "vmotion_rate": DrsConfig.vmotionRate if hasattr(DrsConfig, 'vmotionRate') else 5,
                    }
            
            return {}


class MigrationService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def vmotion_precheck(self, vm_id: str, target_host_id: Optional[str] = None, target_cluster_id: Optional[str] = None) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            vms = client.get_all_vms(self.datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            checks = {
                "vm_status": "pass",
                "host_compatibility": "pass",
                "cpu_compatibility": "pass",
                "memory_available": "pass",
                "network_available": "pass",
                "storage_available": "pass",
            }
            
            current_host = None
            if hasattr(vm, 'runtime') and hasattr(vm.runtime, 'host') and vm.runtime.host:
                current_host = vm.runtime.host
            
            if target_host_id:
                target_host = None
                clusters = client.get_all_clusters(self.datacenter)
                for cluster in clusters:
                    for h in cluster.host:
                        if h._GetMoId() == target_host_id:
                            target_host = h
                            break
                
                if not target_host:
                    checks["host_compatibility"] = "fail"
                    checks["error"] = "Target host not found"
                else:
                    if current_host and current_host._GetMoId() == target_host_id:
                        checks["host_compatibility"] = "skip"
                        checks["reason"] = "Same host"
            
            if target_cluster_id:
                clusters = client.get_all_clusters(self.datacenter)
                target_cluster = None
                for cluster in clusters:
                    if cluster._GetMoId() == target_cluster_id:
                        target_cluster = cluster
                        break
                
                if not target_cluster:
                    checks["host_compatibility"] = "fail"
                    checks["error"] = "Target cluster not found"
            
            return {
                "vm_id": vm_id,
                "vm_name": vm.name,
                "current_host": current_host.name if current_host else None,
                "checks": checks,
                "can_migrate": all(v == "pass" or v == "skip" for v in checks.values())
            }

    def execute_vmotion(self, vm_id: str, target_host_id: str, priority: str = "default") -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            vms = client.get_all_vms(self.datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            clusters = client.get_all_clusters(self.datacenter)
            target_host = None
            for cluster in clusters:
                for h in cluster.host:
                    if h._GetMoId() == target_host_id:
                        target_host = h
                        break
            
            if not target_host:
                raise VSphereOperationError(f"Target host {target_host_id} not found")
            
            priority_flag = {
                "default": None,
                "high": vim.VirtualMachine.MovePriority.highPriority,
                "low": vim.VirtualMachine.MovePriority.lowPriority,
            }.get(priority)
            
            resource_pool = target_host.parent.resourcePool if hasattr(target_host, 'parent') and hasattr(target_host.parent, 'resourcePool') else None
            
            task = vm.migrate(
                pool=resource_pool,
                host=target_host,
                priority=priority_flag
            )
            
            return {
                "task": task,
                "vm_id": vm_id,
                "target_host": target_host.name,
                "status": "initiated"
            }

    def execute_storage_vmotion(self, vm_id: str, target_datastore_name: str) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            vms = client.get_all_vms(self.datacenter)
            vm = None
            for v in vms:
                if v._GetMoId() == vm_id:
                    vm = v
                    break
            
            if not vm:
                raise VSphereOperationError(f"VM {vm_id} not found")
            
            target_datastore = client.get_datastore(target_datastore_name, self.datacenter)
            if not target_datastore:
                raise VSphereOperationError(f"Datastore {target_datastore_name} not found")
            
            reloc_spec = vim.vm.RelocateSpec()
            reloc_spec.datastore = target_datastore
            
            task = vm.RelocateVM_Task(spec=reloc_spec)
            
            return {
                "task": task,
                "vm_id": vm_id,
                "target_datastore": target_datastore_name,
                "status": "initiated"
            }


class ResourcePoolService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def list_resource_pools(self, cluster_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            result = []
            
            if cluster_id:
                clusters = client.get_all_clusters(self.datacenter)
                target_cluster = None
                for cluster in clusters:
                    if cluster._GetMoId() == cluster_id:
                        target_cluster = cluster
                        break
                
                if target_cluster and hasattr(target_cluster, 'resourcePool'):
                    result.append(self._format_resource_pool(target_cluster.resourcePool, ""))
            else:
                clusters = client.get_all_clusters(self.datacenter)
                for cluster in clusters:
                    if hasattr(cluster, 'resourcePool'):
                        result.append(self._format_resource_pool(cluster.resourcePool, ""))
            
            return result

    def _format_resource_pool(self, rp: Any, parent_path: str) -> Dict[str, Any]:
        return {
            "id": rp._GetMoId(),
            "name": rp.name,
            "path": parent_path + "/" + rp.name if parent_path else rp.name,
            "cpu": {
                "reservation": rp.config.cpuAllocation.reservation if hasattr(rp, 'config') and hasattr(rp.config, 'cpuAllocation') and hasattr(rp.config.cpuAllocation, 'reservation') else 0,
                "limit": rp.config.cpuAllocation.limit if hasattr(rp, 'config') and hasattr(rp.config, 'cpuAllocation') and hasattr(rp.config.cpuAllocation, 'limit') else -1,
                "shares": rp.config.cpuAllocation.shares.shares if hasattr(rp, 'config') and hasattr(rp.config, 'cpuAllocation') and hasattr(rp.config.cpuAllocation, 'shares') and hasattr(rp.config.cpuAllocation.shares, 'shares') else 0,
            },
            "memory": {
                "reservation": rp.config.memoryAllocation.reservation if hasattr(rp, 'config') and hasattr(rp.config, 'memoryAllocation') and hasattr(rp.config.memoryAllocation, 'reservation') else 0,
                "limit": rp.config.memoryAllocation.limit if hasattr(rp, 'config') and hasattr(rp.config, 'memoryAllocation') and hasattr(rp.config.memoryAllocation, 'limit') else -1,
                "shares": rp.config.memoryAllocation.shares.shares if hasattr(rp, 'config') and hasattr(rp.config, 'memoryAllocation') and hasattr(rp.config.memoryAllocation, 'shares') and hasattr(rp.config.memoryAllocation.shares, 'shares') else 0,
            }
        }
