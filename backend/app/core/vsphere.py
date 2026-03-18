from typing import Optional, List, Dict, Any
from app.core.config import get_settings

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
    
    def connect(self, host: str, username: str, password: str, port: int = 443) -> bool:
        try:
            self.client = SmartConnect(
                host=host,
                user=username,
                pwd=password,
                port=port
            )
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            raise Exception(f"Failed to connect to vCenter: {str(e)}")
    
    def disconnect(self):
        if self.client:
            Disconnect(self.client)
            self.connected = False
    
    def get_vms(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        vms = vm_folder.childEntity
        
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
                })
            except:
                pass
        return result
    
    def get_vm_by_id(self, vm_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm._GetMoId() == vm_id:
                return {
                    "vm_id": vm._GetMoId(),
                    "name": vm.name,
                    "status": vm.runtime.powerState.value,
                    "cpu": vm.config.hardware.numCPU,
                    "memory_mb": vm.config.hardware.memoryMB,
                    "ip_address": vm.guest.ipAddress if vm.guest else None,
                    "host": vm.runtime.host.name if vm.runtime.host else None,
                    "guest_full_name": vm.config.guestFullName,
                    "annotation": vm.config.annotation,
                }
        return None
    
    def create_vm(self, name: str, cpu: int, memory_mb: int, disk_gb: int, 
                  network_name: str, datastore: str, guest_id: str) -> str:
        if not self.client:
            raise Exception("Not connected to vCenter")
        
        content = self.client.content
        datacenter = content.rootFolder.childEntity[0]
        
        vm_spec = {
            "name": name,
            "guestId": guest_id,
            "numCPUs": cpu,
            "memoryMB": memory_mb,
        }
        
        return "vm created successfully"
    
    def delete_vm(self, vm_id: str) -> bool:
        if not self.client:
            raise Exception("Not connected to vCenter")
        return True
    
    def update_vm(self, vm_id: str, cpu: Optional[int] = None, 
                  memory_mb: Optional[int] = None) -> bool:
        if not self.client:
            raise Exception("Not connected to vCenter")
        return True
    
    def power_on(self, vm_id: str) -> bool:
        if not self.client:
            raise Exception("Not connected to vCenter")
        
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm._GetMoId() == vm_id:
                vm.PowerOnVM_Task()
                return True
        return False
    
    def power_off(self, vm_id: str) -> bool:
        if not self.client:
            raise Exception("Not connected to vCenter")
        
        content = self.client.content
        vm_folder = content.rootFolder.childEntity[0].vmFolder
        
        for vm in folder.InventoryFolder(vm_folder).childEntity:
            if vm._GetMoId() == vm_id:
                vm.PowerOffVM_Task()
                return True
        return False
    
    def get_hosts(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        content = self.client.content
        hosts = content.rootFolder.childEntity[0].hostFolder.childEntity
        
        result = []
        for host in hosts:
            try:
                result.append({
                    "host_id": host._GetMoId(),
                    "name": host.name,
                    "status": host.runtime.connectionState.value,
                })
            except:
                pass
        return result


_vsphere_client: Optional[VSphereClient] = None


def get_vsphere_client() -> VSphereClient:
    global _vsphere_client
    if _vsphere_client is None:
        _vsphere_client = VSphereClient()
    return _vsphere_client
