import logging
from typing import Optional, Dict, Any, List

from app.core.vsphere.client import get_vsphere_client
from app.core.vsphere.exceptions import VSphereOperationError

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def list_datastores(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            datastores = client.get_all_datastores(self.datacenter)
            result = []
            
            for ds in datastores:
                try:
                    summary = client.get_datastore_summary(ds)
                    
                    hosts = []
                    if hasattr(ds, 'host'):
                        for host in ds.host:
                            hosts.append({
                                "id": host.key._GetMoId(),
                                "name": host.key.name
                            })
                    
                    vms = []
                    if hasattr(ds, 'vm'):
                        for vm in ds.vm:
                            vms.append({
                                "id": vm._GetMoId(),
                                "name": vm.name
                            })
                    
                    result.append({
                        **summary,
                        "hosts": hosts,
                        "vms": vms,
                        "type": summary.get("type", "unknown")
                    })
                except Exception as e:
                    logger.error(f"Error formatting datastore {ds.name}: {e}")
            
            return result

    def get_datastore(self, datastore_id: str) -> Optional[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            datastores = client.get_all_datastores(self.datacenter)
            
            for ds in datastores:
                if ds._GetMoId() == datastore_id:
                    return client.get_datastore_summary(ds)
            
            return None

    def get_datastore_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            ds = client.get_datastore(name, self.datacenter)
            if ds:
                return client.get_datastore_summary(ds)
            return None

    def get_storage_overview(self) -> Dict[str, Any]:
        datastores = self.list_datastores()
        
        total_capacity_gb = sum(ds.get("capacity_gb", 0) for ds in datastores)
        total_free_gb = sum(ds.get("free_gb", 0) for ds in datastores)
        total_used_gb = total_capacity_gb - total_free_gb
        
        by_type = {}
        for ds in datastores:
            ds_type = ds.get("type", "unknown")
            if ds_type not in by_type:
                by_type[ds_type] = {
                    "count": 0,
                    "total_gb": 0,
                    "free_gb": 0
                }
            by_type[ds_type]["count"] += 1
            by_type[ds_type]["total_gb"] += ds.get("capacity_gb", 0)
            by_type[ds_type]["free_gb"] += ds.get("free_gb", 0)
        
        return {
            "total_datastores": len(datastores),
            "total_capacity_gb": round(total_capacity_gb, 2),
            "total_free_gb": round(total_free_gb, 2),
            "total_used_gb": round(total_used_gb, 2),
            "usage_percent": round(total_used_gb / total_capacity_gb * 100, 2) if total_capacity_gb > 0 else 0,
            "by_type": by_type,
            "datastores": datastores
        }
