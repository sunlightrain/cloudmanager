import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.vsphere import get_vsphere_client, VSphereOperationError

logger = logging.getLogger(__name__)


class NetworkService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def get_network_detail(self, network_id: str) -> Optional[Dict[str, Any]]:
        try:
            networks = self.vsphere.get_networks()
            for network in networks:
                if network.get("network_id") == network_id:
                    return network
            return None
        except Exception as e:
            logger.error(f"Error getting network detail for {network_id}: {e}")
            return None
    
    def get_network_vms(self, network_id: str) -> List[Dict[str, Any]]:
        try:
            vms = self.vsphere.get_vms()
            result = []
            for vm in vms:
                vm_detail = self.vsphere.get_vm_by_id(vm.get("vm_id"))
                if vm_detail and hasattr(vm_detail, 'num_ethernet_cards'):
                    result.append(vm)
            return result
        except Exception as e:
            logger.error(f"Error getting VMs on network {network_id}: {e}")
            return []
    
    async def add_nic(self, vm_id: str, network_id: str, adapter_type: str = "vmxnet3") -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            network = self.vsphere._find_network_by_id(network_id)
            if not network:
                return {"success": False, "message": "Network not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            nic_spec = vim.VirtualDeviceConfigSpec()
            nic_spec.operation = vim.VirtualDeviceConfigSpecOperation.add
            
            nic = vim.VirtualPCNet32()
            nic.key = -1
            nic.addressType = "generated"
            
            if hasattr(network, 'config') and hasattr(network.config, 'distributedVirtualPortgroup'):
                backing = vim.VirtualEthernetCardDistributedVirtualPortBackingInfo()
                backing.port = vim.DistributedVirtualSwitchPortConnection(
                    switchUuid=network.config.distributedVirtualSwitch.uuid,
                    portgroupKey=network.config.key
                )
                nic.backing = backing
            else:
                backing = vim.VirtualEthernetCardNetworkBackingInfo()
                backing.deviceName = network.name
                nic.backing = backing
            
            nic_spec.device = nic
            spec.deviceChange.append(nic_spec)
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "NIC added", "network_id": network_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to add NIC to VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error adding NIC to VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def remove_nic(self, vm_id: str, nic_mac: str) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            for device in vm.config.hardware.device:
                if hasattr(device, 'macAddress') and device.macAddress == nic_mac:
                    nic_spec = vim.VirtualDeviceConfigSpec()
                    nic_spec.operation = vim.VirtualDeviceConfigSpecOperation.remove
                    nic_spec.device = device
                    spec.deviceChange.append(nic_spec)
                    break
            
            if not spec.deviceChange:
                return {"success": False, "message": "NIC not found"}
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "NIC removed"}
        except VSphereOperationError as e:
            logger.error(f"Failed to remove NIC from VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error removing NIC from VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def update_nic(self, vm_id: str, nic_mac: str, network_id: str = None, connected: bool = None) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            for device in vm.config.hardware.device:
                if hasattr(device, 'macAddress') and device.macAddress == nic_mac:
                    nic_spec = vim.VirtualDeviceConfigSpec()
                    nic_spec.operation = vim.VirtualDeviceConfigSpecOperation.edit
                    nic_spec.device = device
                    
                    if network_id:
                        network = self.vsphere._find_network_by_id(network_id)
                        if network:
                            if hasattr(network, 'config') and hasattr(network.config, 'distributedVirtualPortgroup'):
                                backing = vim.VirtualEthernetCardDistributedVirtualPortBackingInfo()
                                backing.port = vim.DistributedVirtualSwitchPortConnection(
                                    switchUuid=network.config.distributedVirtualSwitch.uuid,
                                    portgroupKey=network.config.key
                                )
                                device.backing = backing
                            else:
                                backing = vim.VirtualEthernetCardNetworkBackingInfo()
                                backing.deviceName = network.name
                                device.backing = backing
                    
                    if connected is not None:
                        device.connectable.startConnected = connected
                    
                    spec.deviceChange.append(nic_spec)
                    break
            
            if not spec.deviceChange:
                return {"success": False, "message": "NIC not found"}
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "NIC updated"}
        except VSphereOperationError as e:
            logger.error(f"Failed to update NIC on VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error updating NIC on VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    def _find_network_by_id(self, network_id: str):
        try:
            content = self.vsphere._client.content
            networks = content.rootFolder.childEntity[0].networkFolder.childEntity
            for network in networks:
                if network._GetMoId() == network_id:
                    return network
            return None
        except Exception as e:
            logger.error(f"Error finding network {network_id}: {e}")
            return None
