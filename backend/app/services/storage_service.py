import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.vsphere import get_vsphere_client, VSphereOperationError
from app.models.storage import Datastore

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    def get_datastore_detail(self, datastore_id: str) -> Optional[Dict[str, Any]]:
        try:
            datastores = self.vsphere.get_datastores()
            for ds in datastores:
                if ds.get("datastore_id") == datastore_id:
                    return ds
            return None
        except Exception as e:
            logger.error(f"Error getting datastore detail for {datastore_id}: {e}")
            return None
    
    def get_datastore_vms(self, datastore_id: str) -> List[Dict[str, Any]]:
        try:
            vms = self.vsphere.get_vms()
            result = []
            for vm in vms:
                if datastore_id in (vm.get("datastore") or "").split(","):
                    result.append(vm)
            return result
        except Exception as e:
            logger.error(f"Error getting VMs on datastore {datastore_id}: {e}")
            return []
    
    async def attach_disk(
        self,
        vm_id: str,
        datastore_id: str,
        disk_size_gb: int,
        disk_type: str = "thin"
    ) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            datastore = self.vsphere._find_datastore_by_id(datastore_id)
            if not datastore:
                return {"success": False, "message": "Datastore not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            unit_number = 0
            for device in vm.config.hardware.device:
                if hasattr(device, 'unitNumber'):
                    unit_number = max(unit_number, device.unitNumber)
            unit_number += 1
            if unit_number > 15:
                unit_number = 16
            
            controller_key = 1000
            for device in vm.config.hardware.device:
                if hasattr(device, 'controllerKey') and device.controllerKey == 1000:
                    controller_key = device.key
                    break
            
            disk_spec = vim.VirtualDeviceConfigSpec()
            disk_spec.operation = vim.VirtualDeviceConfigSpecOperation.add
            disk_spec.fileOperation = vim.VirtualDeviceConfigSpecFileOperation.create
            
            disk = vim.VirtualDisk()
            disk.capacityInKB = disk_size_gb * 1024 * 1024
            disk.key = -1
            disk.unitNumber = unit_number
            disk.controllerKey = controller_key
            
            if disk_type == "thin":
                disk_spec.device = disk
            else:
                disk_backing = vim.VirtualDiskFlatVer2BackingInfo()
                disk_backing.thinProvisioned = False
                disk_backing.eagerlyScrub = True
                disk.device = disk_backing
                disk_spec.device = disk
            
            spec.deviceChange.append(disk_spec)
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "Disk attached", "datastore_id": datastore_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to attach disk to VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error attaching disk to VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def detach_disk(self, vm_id: str, disk_label: str) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            for device in vm.config.hardware.device:
                if hasattr(device, 'deviceInfo') and hasattr(device.deviceInfo, 'label'):
                    if device.deviceInfo.label == disk_label:
                        disk_spec = vim.VirtualDeviceConfigSpec()
                        disk_spec.operation = vim.VirtualDeviceConfigSpecOperation.remove
                        disk_spec.device = device
                        spec.deviceChange.append(disk_spec)
                        break
            
            if not spec.deviceChange:
                return {"success": False, "message": "Disk not found"}
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "Disk detached"}
        except VSphereOperationError as e:
            logger.error(f"Failed to detach disk from VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error detaching disk from VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def resize_disk(self, vm_id: str, disk_label: str, new_size_gb: int) -> Dict[str, Any]:
        try:
            from pyVmomi import vim
            
            vm = self.vsphere._find_vm(vm_id)
            if not vm:
                return {"success": False, "message": "VM not found"}
            
            spec = vim.VirtualMachineConfigSpec()
            spec.deviceChange = []
            
            for device in vm.config.hardware.device:
                if hasattr(device, 'deviceInfo') and hasattr(device.deviceInfo, 'label'):
                    if device.deviceInfo.label == disk_label and hasattr(device, 'capacityInKB'):
                        device.capacityInKB = new_size_gb * 1024 * 1024
                        
                        disk_spec = vim.VirtualDeviceConfigSpec()
                        disk_spec.operation = vim.VirtualDeviceConfigSpecOperation.edit
                        disk_spec.device = device
                        spec.deviceChange.append(disk_spec)
                        break
            
            if not spec.deviceChange:
                return {"success": False, "message": "Disk not found"}
            
            task = vm.Reconfigure(spec)
            self.vsphere._wait_for_task(task)
            
            return {"success": True, "message": "Disk resized"}
        except VSphereOperationError as e:
            logger.error(f"Failed to resize disk on VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error resizing disk on VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
