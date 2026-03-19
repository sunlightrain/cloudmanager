from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.tenant import Tenant, TenantUser
from app.models.vm import VM
from app.models.user import User


class TenantService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_tenant_tree(self) -> List[Dict[str, Any]]:
        tenants = self.session.query(Tenant).filter(Tenant.parent_id == None).all()
        return [self._build_tree(t) for t in tenants]
    
    def _build_tree(self, tenant: Tenant) -> Dict[str, Any]:
        children = self.session.query(Tenant).filter(Tenant.parent_id == tenant.id).all()
        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "level": tenant.level,
            "quota": {
                "cpu": tenant.quota_cpu,
                "memory_gb": tenant.quota_memory_gb,
                "storage_gb": tenant.quota_storage_gb,
                "vm_count": tenant.quota_vm_count
            },
            "children": [self._build_tree(c) for c in children]
        }
    
    def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        return self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def get_tenant_by_code(self, code: str) -> Optional[Tenant]:
        return self.session.query(Tenant).filter(Tenant.code == code).first()
    
    def create_tenant(
        self,
        name: str,
        code: str,
        parent_id: int = None,
        quota_cpu: int = 100,
        quota_memory_gb: int = 512,
        quota_storage_gb: int = 1000,
        quota_vm_count: int = 50
    ) -> Tenant:
        level = 0
        if parent_id:
            parent = self.get_tenant(parent_id)
            if parent:
                level = parent.level + 1
        
        tenant = Tenant(
            name=name,
            code=code,
            parent_id=parent_id,
            level=level,
            quota_cpu=quota_cpu,
            quota_memory_gb=quota_memory_gb,
            quota_storage_gb=quota_storage_gb,
            quota_vm_count=quota_vm_count
        )
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant
    
    def update_tenant(
        self,
        tenant_id: int,
        name: str = None,
        quota_cpu: int = None,
        quota_memory_gb: int = None,
        quota_storage_gb: int = None,
        quota_vm_count: int = None,
        is_active: bool = None
    ) -> Optional[Tenant]:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        if name is not None:
            tenant.name = name
        if quota_cpu is not None:
            tenant.quota_cpu = quota_cpu
        if quota_memory_gb is not None:
            tenant.quota_memory_gb = quota_memory_gb
        if quota_storage_gb is not None:
            tenant.quota_storage_gb = quota_storage_gb
        if quota_vm_count is not None:
            tenant.quota_vm_count = quota_vm_count
        if is_active is not None:
            tenant.is_active = is_active
        
        self.session.commit()
        return tenant
    
    def delete_tenant(self, tenant_id: int) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        children = self.session.query(Tenant).filter(Tenant.parent_id == tenant_id).all()
        if children:
            return False
        
        self.session.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).delete()
        self.session.delete(tenant)
        self.session.commit()
        return True
    
    def add_user_to_tenant(self, tenant_id: int, user_id: int, role: str = "member") -> TenantUser:
        existing = self.session.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id
        ).first()
        if existing:
            existing.role = role
            self.session.commit()
            return existing
        
        tu = TenantUser(tenant_id=tenant_id, user_id=user_id, role=role)
        self.session.add(tu)
        self.session.commit()
        self.session.refresh(tu)
        return tu
    
    def remove_user_from_tenant(self, tenant_id: int, user_id: int) -> bool:
        tu = self.session.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id
        ).first()
        if tu:
            self.session.delete(tu)
            self.session.commit()
            return True
        return False
    
    def get_tenant_users(self, tenant_id: int) -> List[Dict[str, Any]]:
        tus = self.session.query(TenantUser, User).join(
            User, TenantUser.user_id == User.id
        ).filter(TenantUser.tenant_id == tenant_id).all()
        
        return [
            {
                "user_id": tu.user_id,
                "username": user.username,
                "email": user.email,
                "role": tu.role
            }
            for tu, user in tus
        ]
    
    def get_user_tenants(self, user_id: int) -> List[Tenant]:
        tus = self.session.query(TenantUser).filter(TenantUser.user_id == user_id).all()
        tenant_ids = [tu.tenant_id for tu in tus]
        if not tenant_ids:
            return []
        return self.session.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()
    
    def get_tenant_quota_usage(self, tenant_id: int) -> Dict[str, Any]:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        child_ids = self._get_all_child_ids(tenant_id)
        all_ids = [tenant_id] + child_ids
        
        total_cpu = 0
        total_memory_mb = 0
        total_disk_gb = 0
        total_vm_count = 0
        
        vms = self.session.query(VM).filter(VM.tenant_id.in_(all_ids)).all() if all_ids else []
        for vm in vms:
            total_cpu += vm.cpu
            total_memory_mb += vm.memory_mb
            total_vm_count += 1
        
        return {
            "tenant_id": tenant_id,
            "quota": {
                "cpu": tenant.quota_cpu,
                "memory_gb": tenant.quota_memory_gb,
                "storage_gb": tenant.quota_storage_gb,
                "vm_count": tenant.quota_vm_count
            },
            "usage": {
                "cpu": total_cpu,
                "memory_gb": total_memory_mb / 1024,
                "storage_gb": total_disk_gb,
                "vm_count": total_vm_count
            },
            "available": {
                "cpu": max(0, tenant.quota_cpu - total_cpu),
                "memory_gb": max(0, tenant.quota_memory_gb - total_memory_mb / 1024),
                "storage_gb": max(0, tenant.quota_storage_gb - total_disk_gb),
                "vm_count": max(0, tenant.quota_vm_count - total_vm_count)
            }
        }
    
    def _get_all_child_ids(self, tenant_id: int) -> List[int]:
        children = self.session.query(Tenant).filter(Tenant.parent_id == tenant_id).all()
        result = [c.id for c in children]
        for child in children:
            result.extend(self._get_all_child_ids(child.id))
        return result
    
    def check_quota(self, tenant_id: int, cpu: int = 0, memory_mb: int = 0, disk_gb: int = 0, vm_count: int = 0) -> Dict[str, Any]:
        usage = self.get_tenant_quota_usage(tenant_id)
        if not usage:
            return {"allowed": False, "reason": "Tenant not found"}
        
        quota = usage["quota"]
        available = usage["available"]
        
        if cpu > available["cpu"]:
            return {"allowed": False, "reason": f"CPU quota exceeded. Available: {available['cpu']}, Requested: {cpu}"}
        if memory_mb / 1024 > available["memory_gb"]:
            return {"allowed": False, "reason": f"Memory quota exceeded. Available: {available['memory_gb']} GB, Requested: {memory_mb / 1024} GB"}
        if disk_gb > available["storage_gb"]:
            return {"allowed": False, "reason": f"Storage quota exceeded. Available: {available['storage_gb']} GB, Requested: {disk_gb}"}
        if vm_count > available["vm_count"]:
            return {"allowed": False, "reason": f"VM count quota exceeded. Available: {available['vm_count']}, Requested: {vm_count}"}
        
        return {"allowed": True}
    
    def get_accessible_tenant_ids(self, user_id: int, user_role: str = "member") -> List[int]:
        if user_role == "admin":
            tenants = self.session.query(Tenant).all()
            return [t.id for t in tenants]
        
        tus = self.session.query(TenantUser).filter(TenantUser.user_id == user_id).all()
        tenant_ids = []
        for tu in tus:
            tenant_ids.append(tu.tenant_id)
            tenant_ids.extend(self._get_all_child_ids(tu.tenant_id))
        return list(set(tenant_ids))
