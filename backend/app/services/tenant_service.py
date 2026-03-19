import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.enterprise import (
    Organization, OrganizationUser, TenantVM, User
)

logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, session: Session):
        self.session = session

    def create_organization(
        self,
        name: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
        quota: Optional[Dict[str, Any]] = None
    ) -> Organization:
        level = 1
        if parent_id:
            parent = self.session.get(Organization, parent_id)
            if parent:
                level = parent.level + 1
        
        org = Organization(
            uuid=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            level=level,
            description=description,
            quota=quota or {
                "cpu_cores": 100,
                "memory_gb": 512,
                "storage_tb": 10,
                "vm_count": 50
            }
        )
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        return org

    def get_organization(self, org_id: int) -> Optional[Organization]:
        return self.session.get(Organization, org_id)

    def get_organization_by_uuid(self, uuid: str) -> Optional[Organization]:
        return self.session.query(Organization).filter(Organization.uuid == uuid).first()

    def list_organizations(self, parent_id: Optional[int] = None) -> List[Organization]:
        query = self.session.query(Organization)
        if parent_id:
            query = query.filter(Organization.parent_id == parent_id)
        return query.all()

    def update_organization(
        self,
        org_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        quota: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Organization]:
        org = self.session.get(Organization, org_id)
        if not org:
            return None
        
        if name is not None:
            org.name = name
        if description is not None:
            org.description = description
        if quota is not None:
            org.quota = quota
        if is_active is not None:
            org.is_active = is_active
        org.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(org)
        return org

    def delete_organization(self, org_id: int) -> bool:
        org = self.session.get(Organization, org_id)
        if not org:
            return False
        
        children = self.session.query(Organization).filter(Organization.parent_id == org_id).all()
        if children:
            logger.warning(f"Cannot delete organization {org_id}: has {len(children)} children")
            return False
        
        self.session.delete(org)
        self.session.commit()
        return True

    def get_quota_usage(self, org_id: int) -> Dict[str, Any]:
        org = self.session.get(Organization, org_id)
        if not org:
            return {}
        
        tenant_vms = self.session.query(TenantVM).filter(TenantVM.organization_id == org_id).all()
        
        used_cpu = sum(vm.cpu for vm in tenant_vms)
        used_memory = sum(vm.memory_mb for vm in tenant_vms) / 1024
        used_storage = sum(vm.disk_gb for vm in tenant_vms) / 1024
        used_vm_count = len(tenant_vms)
        
        quota = org.quota
        return {
            "cpu_cores": {
                "limit": quota.get("cpu_cores", 100),
                "used": used_cpu,
                "available": quota.get("cpu_cores", 100) - used_cpu,
                "usage_percent": round(used_cpu / quota.get("cpu_cores", 100) * 100, 2) if quota.get("cpu_cores") else 0
            },
            "memory_gb": {
                "limit": quota.get("memory_gb", 512),
                "used": round(used_memory, 2),
                "available": round(quota.get("memory_gb", 512) - used_memory, 2),
                "usage_percent": round(used_memory / quota.get("memory_gb", 512) * 100, 2) if quota.get("memory_gb") else 0
            },
            "storage_tb": {
                "limit": quota.get("storage_tb", 10),
                "used": round(used_storage, 2),
                "available": round(quota.get("storage_tb", 10) - used_storage, 2),
                "usage_percent": round(used_storage / quota.get("storage_tb", 10) * 100, 2) if quota.get("storage_tb") else 0
            },
            "vm_count": {
                "limit": quota.get("vm_count", 50),
                "used": used_vm_count,
                "available": quota.get("vm_count", 50) - used_vm_count,
                "usage_percent": round(used_vm_count / quota.get("vm_count", 50) * 100, 2) if quota.get("vm_count") else 0
            }
        }

    def check_quota(
        self,
        org_id: int,
        cpu: int = 0,
        memory_gb: float = 0,
        storage_tb: float = 0
    ) -> tuple[bool, Optional[str]]:
        usage = self.get_quota_usage(org_id)
        
        if usage["cpu_cores"]["used"] + cpu > usage["cpu_cores"]["limit"]:
            return False, f"CPU quota exceeded. Available: {usage['cpu_cores']['available']}"
        
        if usage["memory_gb"]["used"] + memory_gb > usage["memory_gb"]["limit"]:
            return False, f"Memory quota exceeded. Available: {usage['memory_gb']['available']} GB"
        
        if usage["storage_tb"]["used"] + storage_tb > usage["storage_tb"]["limit"]:
            return False, f"Storage quota exceeded. Available: {usage['storage_tb']['available']} TB"
        
        return True, None


class TenantVMService:
    def __init__(self, session: Session):
        self.session = session

    def create_vm(
        self,
        organization_id: int,
        vm_id: str,
        name: str,
        cpu: int,
        memory_mb: int,
        disk_gb: int,
        status: str = "unknown",
        ip_address: Optional[str] = None
    ) -> TenantVM:
        tenant_vm = TenantVM(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            vm_id=vm_id,
            name=name,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            status=status,
            ip_address=ip_address
        )
        self.session.add(tenant_vm)
        self.session.commit()
        self.session.refresh(tenant_vm)
        return tenant_vm

    def get_vm(self, vm_id: int) -> Optional[TenantVM]:
        return self.session.get(TenantVM, vm_id)

    def get_vm_by_uuid(self, uuid: str) -> Optional[TenantVM]:
        return self.session.query(TenantVM).filter(TenantVM.uuid == uuid).first()

    def get_vm_by_vm_id(self, vm_id: str) -> Optional[TenantVM]:
        return self.session.query(TenantVM).filter(TenantVM.vm_id == vm_id).first()

    def list_vms(self, organization_id: Optional[int] = None) -> List[TenantVM]:
        query = self.session.query(TenantVM)
        if organization_id:
            query = query.filter(TenantVM.organization_id == organization_id)
        return query.all()

    def update_vm(
        self,
        vm_id: int,
        cpu: Optional[int] = None,
        memory_mb: Optional[int] = None,
        disk_gb: Optional[int] = None,
        status: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[TenantVM]:
        tenant_vm = self.session.get(TenantVM, vm_id)
        if not tenant_vm:
            return None
        
        if cpu is not None:
            tenant_vm.cpu = cpu
        if memory_mb is not None:
            tenant_vm.memory_mb = memory_mb
        if disk_gb is not None:
            tenant_vm.disk_gb = disk_gb
        if status is not None:
            tenant_vm.status = status
        if ip_address is not None:
            tenant_vm.ip_address = ip_address
        tenant_vm.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(tenant_vm)
        return tenant_vm

    def delete_vm(self, vm_id: int) -> bool:
        tenant_vm = self.session.get(TenantVM, vm_id)
        if not tenant_vm:
            return False
        
        self.session.delete(tenant_vm)
        self.session.commit()
        return True

    def get_org_vms_by_vsphere_vm_id(self, organization_id: int, vsphere_vm_id: str) -> Optional[TenantVM]:
        return self.session.query(TenantVM).filter(
            TenantVM.organization_id == organization_id,
            TenantVM.vm_id == vsphere_vm_id
        ).first()
