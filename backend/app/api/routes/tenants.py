from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.services.tenant_service import TenantService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("", response_model=ResponseModel)
def list_tenants(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    tenant_service = TenantService(session)
    
    if current_user.role == "admin":
        tenants = session.query(Tenant).all()
    else:
        tenant_ids = tenant_service.get_accessible_tenant_ids(current_user.id, current_user.role)
        tenants = session.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all() if tenant_ids else []
    
    return ResponseModel(data=[t.model_dump() for t in tenants])


@router.post("", response_model=ResponseModel)
def create_tenant(
    name: str,
    code: str,
    parent_id: Optional[int] = None,
    quota_cpu: int = 100,
    quota_memory_gb: int = 512,
    quota_storage_gb: int = 1000,
    quota_vm_count: int = 50,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    tenant_service = TenantService(session)
    tenant = tenant_service.create_tenant(
        name=name,
        code=code,
        parent_id=parent_id,
        quota_cpu=quota_cpu,
        quota_memory_gb=quota_memory_gb,
        quota_storage_gb=quota_storage_gb,
        quota_vm_count=quota_vm_count
    )
    return ResponseModel(data=tenant.model_dump())


@router.get("/tree", response_model=ResponseModel)
def get_tenant_tree(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    tenant_service = TenantService(session)
    tree = tenant_service.get_tenant_tree()
    return ResponseModel(data=tree)


@router.get("/{tenant_id}", response_model=ResponseModel)
def get_tenant(
    tenant_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    tenant_service = TenantService(session)
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return ResponseModel(data=tenant.model_dump())


@router.put("/{tenant_id}", response_model=ResponseModel)
def update_tenant(
    tenant_id: int,
    name: Optional[str] = None,
    quota_cpu: Optional[int] = None,
    quota_memory_gb: Optional[int] = None,
    quota_storage_gb: Optional[int] = None,
    quota_vm_count: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    tenant_service = TenantService(session)
    tenant = tenant_service.update_tenant(
        tenant_id=tenant_id,
        name=name,
        quota_cpu=quota_cpu,
        quota_memory_gb=quota_memory_gb,
        quota_storage_gb=quota_storage_gb,
        quota_vm_count=quota_vm_count,
        is_active=is_active
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return ResponseModel(data=tenant.model_dump())


@router.delete("/{tenant_id}", response_model=ResponseModel)
def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    tenant_service = TenantService(session)
    success = tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete tenant with children")
    return ResponseModel(message="Tenant deleted")


@router.get("/{tenant_id}/quota", response_model=ResponseModel)
def get_tenant_quota(
    tenant_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    tenant_service = TenantService(session)
    quota = tenant_service.get_tenant_quota_usage(tenant_id)
    if not quota:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return ResponseModel(data=quota)


@router.get("/{tenant_id}/users", response_model=ResponseModel)
def get_tenant_users(
    tenant_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    tenant_service = TenantService(session)
    users = tenant_service.get_tenant_users(tenant_id)
    return ResponseModel(data=users)


@router.post("/{tenant_id}/users", response_model=ResponseModel)
def add_tenant_user(
    tenant_id: int,
    user_id: int,
    role: str = "member",
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    tenant_service = TenantService(session)
    tu = tenant_service.add_user_to_tenant(tenant_id, user_id, role)
    return ResponseModel(data={"user_id": tu.user_id, "role": tu.role})


@router.delete("/{tenant_id}/users/{user_id}", response_model=ResponseModel)
def remove_tenant_user(
    tenant_id: int,
    user_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    tenant_service = TenantService(session)
    success = tenant_service.remove_user_from_tenant(tenant_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in tenant")
    return ResponseModel(message="User removed from tenant")


from app.models.tenant import Tenant
