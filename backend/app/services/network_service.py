import logging
from typing import Optional, Dict, Any, List

from app.core.vsphere.client import get_vsphere_client
from app.core.vsphere.exceptions import VSphereOperationError

logger = logging.getLogger(__name__)


class NetworkService:
    def __init__(self, vcenter_config: Dict[str, Any], datacenter: Optional[str] = None):
        self.vcenter_config = vcenter_config
        self.datacenter = datacenter

    def list_networks(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            return client.get_all_networks(self.datacenter)

    def get_network(self, network_id: str) -> Optional[Dict[str, Any]]:
        networks = self.list_networks()
        for network in networks:
            if network.get("network_id") == network_id:
                return network
        return None

    def list_standard_switches(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            dc = client._get_dc(self.datacenter)
            if not dc:
                return []
            
            result = []
            container_view = client._view_manager.CreateContainerView(
                container=dc,
                type=[vim.Network],
                recursive=True
            )
            
            try:
                for network in container_view.view:
                    if not hasattr(network, 'config') or not network.config:
                        result.append({
                            "network_id": network._GetMoId(),
                            "name": network.name,
                            "type": "standard",
                            "accessible": True
                        })
            finally:
                container_view.Destroy()
            
            return result

    def list_distributed_switches(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            dc = client._get_dc(self.datacenter)
            if not dc:
                return []
            
            result = []
            container_view = client._view_manager.CreateContainerView(
                container=dc,
                type=[vim.dvs.VmwareDistributedVirtualSwitch],
                recursive=True
            )
            
            try:
                for dvs in container_view.view:
                    uplinks = []
                    if hasattr(dvs, 'config') and hasattr(dvs.config, 'uplinkPorts'):
                        for uplink in dvs.config.uplinkPorts:
                            uplinks.append({
                                "key": uplink.key,
                                "name": uplink.name if hasattr(uplink, 'name') else uplink.key
                            })
                    
                    result.append({
                        "switch_id": dvs._GetMoId(),
                        "name": dvs.name,
                        "type": "distributed",
                        "num_ports": dvs.config.numPorts if hasattr(dvs, 'config') and hasattr(dvs.config, 'numPorts') else 0,
                        "num_uplink_ports": len(uplinks),
                        "uplinks": uplinks,
                        "product_info": {
                            "version": dvs.config.productInfo.version if hasattr(dvs, 'config') and hasattr(dvs.config, 'productInfo') else "unknown",
                            "edition": dvs.config.productInfo.editionKey if hasattr(dvs, 'config') and hasattr(dvs.config, 'productInfo') else "unknown"
                        } if hasattr(dvs, 'config') and hasattr(dvs.config, 'productInfo') else {}
                    })
            finally:
                container_view.Destroy()
            
            return result

    def list_port_groups(self) -> List[Dict[str, Any]]:
        with get_vsphere_client(**self.vcenter_config, datacenter=self.datacenter) as client:
            from app.core.vsphere.client import vim
            
            dc = client._get_dc(self.datacenter)
            if not dc:
                return []
            
            result = []
            container_view = client._view_manager.CreateContainerView(
                container=dc,
                type=[vim.DistributedVirtualPortgroup],
                recursive=True
            )
            
            try:
                for pg in container_view.view:
                    vlan_info = {}
                    if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') and hasattr(pg.config.defaultPortConfig, 'vlan'):
                        vlan = pg.config.defaultPortConfig.vlan
                        if hasattr(vlan, 'vlanId'):
                            vlan_info = {"type": "vlan", "vlan_id": vlan.vlanId}
                        elif hasattr(vlan, 'vlanId'):
                            vlan_info = {"type": "vlan", "vlan_id": vlan.vlanId}
                    
                    result.append({
                        "portgroup_id": pg._GetMoId(),
                        "name": pg.name,
                        "vlan": vlan_info,
                        "switch": pg.config.distributedVirtualSwitch if hasattr(pg, 'config') and hasattr(pg.config, 'distributedVirtualSwitch') else None,
                        "num_ports": pg.config.numPorts if hasattr(pg, 'config') and hasattr(pg.config, 'numPorts') else 0,
                        "policy": {
                            "security": {
                                "allow_promiscuous": pg.config.defaultPortConfig.securityPolicy.allowPromiscuous if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') and hasattr(pg.config.defaultPortConfig, 'securityPolicy') else False,
                                "forged_transmits": pg.config.defaultPortConfig.securityPolicy.forgedTransmits if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') and hasattr(pg.config.defaultPortConfig, 'securityPolicy') else False,
                                "mac_changes": pg.config.defaultPortConfig.securityPolicy.macChanges if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') and hasattr(pg.config.defaultPortConfig, 'securityPolicy') else False,
                            }
                        } if hasattr(pg, 'config') and hasattr(pg.config, 'defaultPortConfig') else {}
                    })
            finally:
                container_view.Destroy()
            
            return result

    def get_network_overview(self) -> Dict[str, Any]:
        standard_switches = self.list_standard_switches()
        distributed_switches = self.list_distributed_switches()
        port_groups = self.list_port_groups()
        networks = self.list_networks()
        
        return {
            "total_networks": len(networks),
            "standard_switches": {
                "count": len(standard_switches),
                "items": standard_switches
            },
            "distributed_switches": {
                "count": len(distributed_switches),
                "items": distributed_switches
            },
            "port_groups": {
                "count": len(port_groups),
                "items": port_groups
            }
        }
