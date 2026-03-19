import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.vsphere.client import get_vsphere_client
from app.core.vsphere.exceptions import VSphereOperationError

logger = logging.getLogger(__name__)


class DatacenterService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def get_hierarchy_tree(self) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            datacenters = client.get_all_datacenters()
            result = []
            
            for dc in datacenters:
                dc_data = {
                    "id": dc._GetMoId(),
                    "name": dc.name,
                    "type": "datacenter",
                    "children": []
                }
                
                clusters = client.get_all_clusters(dc.name)
                for cluster in clusters:
                    cluster_data = {
                        "id": cluster._GetMoId(),
                        "name": cluster.name,
                        "type": "cluster",
                        "children": []
                    }
                    
                    hosts = client.get_cluster_hosts(cluster)
                    for host in hosts:
                        host_data = self._format_host_tree(host)
                        cluster_data["children"].append(host_data)
                    
                    dc_data["children"].append(cluster_data)
                
                result.append(dc_data)
            
            return {
                "datacenters": result,
                "total_datacenters": len(result),
                "total_clusters": sum(len(dc["children"]) for dc in result),
                "total_hosts": sum(
                    sum(len(c["children"]) for c in dc["children"]) 
                    for dc in result
                )
            }

    def _format_host_tree(self, host) -> Dict[str, Any]:
        try:
            runtime = host.runtime if host.runtime else {}
            hardware = host.hardware if host.hardware else {}
            quick_stats = host.summary.quickStats if hasattr(host, 'summary') and host.summary and hasattr(host.summary, 'quickStats') else {}
            
            return {
                "id": host._GetMoId(),
                "name": host.name,
                "type": "host",
                "status": str(runtime.connectionState.value) if hasattr(runtime, 'connectionState') else "unknown",
                "power_state": str(runtime.powerState.value) if hasattr(runtime, 'powerState') else "unknown",
                "maintenance_mode": runtime.inMaintenanceMode if hasattr(runtime, 'inMaintenanceMode') else False,
                "cpu": {
                    "model": hardware.cpuPkg[0].name if hardware.cpuPkg else "Unknown",
                    "cores": hardware.cpuInfo.numCpuCores if hardware.cpuInfo else 0,
                    "packages": hardware.cpuInfo.numCpuPackages if hardware.cpuInfo else 0,
                },
                "memory": {
                    "total_gb": round(hardware.memorySize / (1024**3), 2) if hardware.memorySize else 0,
                },
                "stats": {
                    "cpu_usage_percent": quick_stats.overallCpuUsage if hasattr(quick_stats, 'overallCpuUsage') else 0,
                    "memory_usage_gb": quick_stats.overallMemoryUsage if hasattr(quick_stats, 'overallMemoryUsage') else 0,
                },
                "datastores": [
                    {
                        "id": ds._GetMoId(),
                        "name": ds.name,
                        "type": "datastore"
                    }
                    for ds in host.datastore if hasattr(host, 'datastore')
                ],
                "networks": [
                    {
                        "id": net._GetMoId(),
                        "name": net.name,
                        "type": "network"
                    }
                    for net in host.network if hasattr(host, 'network')
                ] if hasattr(host, 'network') else []
            }
        except Exception as e:
            logger.error(f"Error formatting host tree: {e}")
            return {
                "id": host._GetMoId(),
                "name": host.name,
                "type": "host",
                "error": str(e)
            }

    def get_datacenter_overview(self, dc_name: str) -> Dict[str, Any]:
        with get_vsphere_client(**self.vcenter_config, datacenter=dc_name) as client:
            dc = client.get_datacenter(dc_name)
            if not dc:
                raise VSphereOperationError(f"Datacenter {dc_name} not found")
            
            clusters = client.get_all_clusters(dc_name)
            all_hosts = []
            all_vms = []
            all_datastores = []
            
            for cluster in clusters:
                hosts = client.get_cluster_hosts(cluster)
                all_hosts.extend(hosts)
                
                for host in hosts:
                    if hasattr(host, 'datastore'):
                        for ds in host.datastore:
                            if ds not in all_datastores:
                                all_datastores.append(ds)
                
                vm_folder = dc.vmFolder
                from app.core.vsphere.client import vim
                container_view = client._view_manager.CreateContainerView(
                    container=vm_folder,
                    type=[vim.VirtualMachine],
                    recursive=True
                )
                try:
                    for vm in container_view.view:
                        if vm.runtime.host in cluster.host:
                            all_vms.append(vm)
                finally:
                    container_view.Destroy()
            
            powered_on = sum(1 for vm in all_vms if hasattr(vm, 'runtime') and hasattr(vm.runtime, 'powerState') and vm.runtime.powerState.value == "poweredOn")
            
            total_cpu_cores = sum(
                h.hardware.cpuInfo.numCpuCores if hasattr(h, 'hardware') and hasattr(h.hardware, 'cpuInfo') else 0
                for h in all_hosts
            )
            total_memory_gb = sum(
                round(h.hardware.memorySize / (1024**3), 2)
                for h in all_hosts
                if hasattr(h, 'hardware') and hasattr(h.hardware, 'memorySize')
            )
            
            total_storage_gb = 0
            free_storage_gb = 0
            for ds in all_datastores:
                try:
                    if hasattr(ds, 'summary') and ds.summary:
                        total_storage_gb += ds.summary.capacity / (1024**3)
                        free_storage_gb += ds.summary.freeSpace / (1024**3)
                except:
                    pass
            
            ha_enabled = any(
                c.summary.haConfig.enabled if hasattr(c, 'summary') and hasattr(c.summary, 'haConfig') else False
                for c in clusters
            )
            drs_enabled = any(
                c.summary.drsConfig.enabled if hasattr(c, 'summary') and hasattr(c.summary, 'drsConfig') else False
                for c in clusters
            )
            
            return {
                "datacenter": {
                    "id": dc._GetMoId(),
                    "name": dc.name,
                },
                "clusters": {
                    "count": len(clusters),
                    "items": [
                        {
                            "id": c._GetMoId(),
                            "name": c.name,
                            "host_count": len(c.host) if hasattr(c, 'host') else 0,
                            "ha_enabled": c.summary.haConfig.enabled if hasattr(c, 'summary') and hasattr(c.summary, 'haConfig') else False,
                            "drs_enabled": c.summary.drsConfig.enabled if hasattr(c, 'summary') and hasattr(c.summary, 'drsConfig') else False,
                        }
                        for c in clusters
                    ]
                },
                "hosts": {
                    "total": len(all_hosts),
                    "powered_on": sum(1 for h in all_hosts if hasattr(h, 'runtime') and hasattr(h.runtime, 'powerState') and h.runtime.powerState.value == "poweredOn"),
                    "maintenance_mode": sum(1 for h in all_hosts if hasattr(h, 'runtime') and hasattr(h.runtime, 'inMaintenanceMode') and h.runtime.inMaintenanceMode),
                },
                "vms": {
                    "total": len(all_vms),
                    "powered_on": powered_on,
                    "powered_off": len(all_vms) - powered_on,
                },
                "storage": {
                    "total_gb": round(total_storage_gb, 2),
                    "free_gb": round(free_storage_gb, 2),
                    "used_gb": round(total_storage_gb - free_storage_gb, 2),
                    "usage_percent": round((total_storage_gb - free_storage_gb) / total_storage_gb * 100, 2) if total_storage_gb > 0 else 0,
                },
                "compute": {
                    "total_cpu_cores": total_cpu_cores,
                    "total_memory_gb": total_memory_gb,
                },
                "features": {
                    "ha_enabled": ha_enabled,
                    "drs_enabled": drs_enabled,
                }
            }
