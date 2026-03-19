import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.vsphere import get_vsphere_client, VSphereOperationError
from app.models.vm import VM

logger = logging.getLogger(__name__)


class VMService:
    def __init__(self, session: Session):
        self.session = session
        self.vsphere = get_vsphere_client()
    
    async def power_on(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.power_on(vm_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM powered on", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to power on VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error powering on VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def power_off(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.power_off(vm_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM powered off", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to power off VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error powering off VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def restart(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.restart_vm(vm_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM restarted", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to restart VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error restarting VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def suspend(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.suspend(vm_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM suspended", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to suspend VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error suspending VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def delete(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.delete_vm(vm_id)
            vm = self.session.query(VM).filter(VM.vc_guid == vm_id).first()
            if vm:
                self.session.delete(vm)
                self.session.commit()
            return {"success": True, "message": "VM deleted", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to delete VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error deleting VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def get_snapshots(self, vm_id: str) -> List[Dict[str, Any]]:
        try:
            return self.vsphere.get_snapshots(vm_id)
        except VSphereOperationError as e:
            logger.error(f"Failed to get snapshots for VM {vm_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting snapshots for VM {vm_id}: {e}")
            return []
    
    async def create_snapshot(self, vm_id: str, name: str, description: str = "", memory: bool = False) -> Dict[str, Any]:
        try:
            result = self.vsphere.create_snapshot(vm_id, name, description, memory)
            return {"success": True, "message": "Snapshot created", "snapshot_name": name}
        except VSphereOperationError as e:
            logger.error(f"Failed to create snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error creating snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.revert_snapshot(vm_id, snapshot_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "Reverted to snapshot", "snapshot_id": snapshot_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to revert snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error reverting snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.delete_snapshot(vm_id, snapshot_id)
            return {"success": True, "message": "Snapshot deleted", "snapshot_id": snapshot_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to delete snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error deleting snapshot for VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def _update_vm_status(self, vm_id: str):
        try:
            vm_data = self.vsphere.get_vm_by_id(vm_id)
            if vm_data:
                vm = self.session.query(VM).filter(VM.vc_guid == vm_id).first()
                if vm:
                    vm.status = vm_data.get("status", "unknown")
                    vm.last_sync = datetime.utcnow()
                    self.session.commit()
        except Exception as e:
            logger.error(f"Failed to update VM status for {vm_id}: {e}")
    
    def get_vm_from_db(self, vm_id: int) -> Optional[VM]:
        return self.session.query(VM).filter(VM.id == vm_id).first()
    
    def get_vm_by_vc_guid(self, vc_guid: str) -> Optional[VM]:
        return self.session.query(VM).filter(VM.vc_guid == vc_guid).first()
    
    def get_vm_detail(self, vm_id: str) -> Optional[Dict[str, Any]]:
        try:
            vm_data = self.vsphere.get_vm_by_id(vm_id)
            if not vm_data:
                vm = self.get_vm_by_vc_guid(vm_id)
                if vm:
                    return vm.__dict__
                return None
            
            vm = self.session.query(VM).filter(VM.vc_guid == vm_id).first()
            if vm:
                vm.last_sync = datetime.utcnow()
                self.session.commit()
            
            return vm_data
        except Exception as e:
            logger.error(f"Failed to get VM detail for {vm_id}: {e}")
            return None
    
    def get_vm_performance(self, vm_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.vsphere.get_vm_performance(vm_id)
        except Exception as e:
            logger.error(f"Failed to get VM performance for {vm_id}: {e}")
            return None
    
    async def migrate(
        self,
        vm_id: str,
        target_host_id: str = None,
        target_datastore_id: str = None,
        target_cluster_id: str = None,
        priority: str = "default"
    ) -> Dict[str, Any]:
        try:
            result = self.vsphere.migrate_vm(
                vm_id=vm_id,
                target_host_id=target_host_id,
                target_datastore_id=target_datastore_id,
                target_cluster_id=target_cluster_id,
                priority=priority
            )
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM migrated", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to migrate VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error migrating VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def storage_vmotion(self, vm_id: str, target_datastore_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.storage_vmotion(vm_id, target_datastore_id)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "Storage vMotion completed", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to perform Storage vMotion for VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error performing Storage vMotion for VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def hot_resize(
        self,
        vm_id: str,
        cpu: int = None,
        memory_mb: int = None,
        disk_gb: int = None
    ) -> Dict[str, Any]:
        try:
            result = self.vsphere.hot_resize(vm_id, cpu=cpu, memory_mb=memory_mb, disk_gb=disk_gb)
            await self._update_vm_status(vm_id)
            return {"success": True, "message": "VM resized", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to hot-resize VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error hot-resizing VM {vm_id}: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def clone(
        self,
        vm_id: str,
        name: str,
        target_host_id: str = None,
        target_datastore_id: str = None,
        target_folder_id: str = None,
        linked_clone: bool = False,
        snapshot_id: str = None
    ) -> Dict[str, Any]:
        try:
            cloned_vm_id = self.vsphere.clone_vm(
                vm_id=vm_id,
                name=name,
                target_host_id=target_host_id,
                target_datastore_id=target_datastore_id,
                target_folder_id=target_folder_id,
                linked_clone=linked_clone,
                snapshot_id=snapshot_id
            )
            return {"success": True, "message": "VM cloned", "cloned_vm_id": cloned_vm_id, "name": name}
        except VSphereOperationError as e:
            logger.error(f"Failed to clone VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error cloning VM {vm_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def convert_to_template(self, vm_id: str) -> Dict[str, Any]:
        try:
            result = self.vsphere.convert_to_template(vm_id)
            return {"success": True, "message": "VM converted to template", "vm_id": vm_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to convert VM {vm_id} to template: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
        except Exception as e:
            logger.error(f"Unexpected error converting VM {vm_id} to template: {e}")
            return {"success": False, "message": str(e), "vm_id": vm_id}
    
    async def convert_to_vm(self, template_id: str, target_host_id: str = None) -> Dict[str, Any]:
        try:
            result = self.vsphere.convert_to_vm(template_id, target_host_id)
            return {"success": True, "message": "Template converted to VM", "vm_id": template_id}
        except VSphereOperationError as e:
            logger.error(f"Failed to convert template {template_id} to VM: {e}")
            return {"success": False, "message": str(e), "vm_id": template_id}
        except Exception as e:
            logger.error(f"Unexpected error converting template {template_id} to VM: {e}")
            return {"success": False, "message": str(e), "vm_id": template_id}
    
    async def batch_power_on(self, vm_ids: List[str]) -> Dict[str, Any]:
        results = []
        for vm_id in vm_ids:
            result = await self.power_on(vm_id)
            results.append(result)
        return {"success": True, "results": results}
    
    async def batch_power_off(self, vm_ids: List[str]) -> Dict[str, Any]:
        results = []
        for vm_id in vm_ids:
            result = await self.power_off(vm_id)
            results.append(result)
        return {"success": True, "results": results}
    
    async def batch_delete(self, vm_ids: List[str]) -> Dict[str, Any]:
        results = []
        for vm_id in vm_ids:
            result = await self.delete(vm_id)
            results.append(result)
        return {"success": True, "results": results}
