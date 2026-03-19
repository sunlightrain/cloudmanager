from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.services.approval_service import ApprovalService
from app.services.tenant_service import TenantService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/templates", response_model=ResponseModel)
def list_templates(
    request_type: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    templates = service.get_templates(request_type)
    return ResponseModel(data=[t.model_dump() for t in templates])


@router.post("/templates", response_model=ResponseModel)
def create_template(
    name: str,
    request_type: str,
    steps: List[dict],
    is_auto_approve: bool = False,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    service = ApprovalService(session)
    template = service.create_template(name, request_type, steps, is_auto_approve)
    return ResponseModel(data=template.model_dump())


@router.get("", response_model=ResponseModel)
def list_requests(
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    tenant_service = TenantService(session)
    
    if not tenant_id:
        tenant_ids = tenant_service.get_accessible_tenant_ids(current_user.id, current_user.role)
        if len(tenant_ids) == 1:
            tenant_id = tenant_ids[0]
    
    requests = service.get_requests(tenant_id, status, request_type)
    return ResponseModel(data=requests)


@router.post("", response_model=ResponseModel)
def create_request(
    request_type: str,
    tenant_id: int,
    resource_type: str,
    resource_id: str,
    detail: dict,
    template_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    tenant_service = TenantService(session)
    
    tenant_ids = tenant_service.get_accessible_tenant_ids(current_user.id, current_user.role)
    if tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="No access to this tenant")
    
    request = service.create_request(
        request_type=request_type,
        tenant_id=tenant_id,
        applicant_id=current_user.id,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        template_id=template_id
    )
    
    request_dict = {
        "id": request.id,
        "request_type": request.request_type,
        "status": request.status,
        "created_at": request.created_at.isoformat() if request.created_at else None
    }
    
    return ResponseModel(data=request_dict)


@router.get("/{request_id}", response_model=ResponseModel)
def get_request(
    request_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    request = service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    tenant_service = TenantService(session)
    tenant_ids = tenant_service.get_accessible_tenant_ids(current_user.id, current_user.role)
    if request.tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="No access")
    
    request_dict = service._request_to_dict(request)
    return ResponseModel(data=request_dict)


@router.post("/{request_id}/approve", response_model=ResponseModel)
def approve_request(
    request_id: int,
    comment: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    result = service.approve(request_id, current_user.id, comment)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ResponseModel(message=result["message"], data=result)


@router.post("/{request_id}/reject", response_model=ResponseModel)
def reject_request(
    request_id: int,
    comment: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    result = service.reject(request_id, current_user.id, comment)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ResponseModel(message=result["message"], data=result)


@router.get("/{request_id}/history", response_model=ResponseModel)
def get_request_history(
    request_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    history = service.get_request_history(request_id)
    return ResponseModel(data=history)


@router.get("/pending/mine", response_model=ResponseModel)
def get_my_pending(
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    service = ApprovalService(session)
    tenant_service = TenantService(session)
    tenant_ids = tenant_service.get_accessible_tenant_ids(current_user.id, current_user.role)
    pending = service.get_pending_requests(current_user.id, tenant_ids)
    return ResponseModel(data=pending)
