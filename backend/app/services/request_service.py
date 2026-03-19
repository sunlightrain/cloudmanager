import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.enterprise import Request, ApprovalAction, Organization
from app.models.user import User
from app.services.tenant_service import OrganizationService, TenantVMService

logger = logging.getLogger(__name__)


class RequestService:
    def __init__(self, session: Session):
        self.session = session

    def create_request(
        self,
        organization_id: int,
        user_id: int,
        request_type: str,
        title: str,
        details: Dict[str, Any],
        approval_chain: Optional[List[int]] = None
    ) -> Request:
        request = Request(
            uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            user_id=user_id,
            type=request_type,
            title=title,
            details=details,
            approval_chain=approval_chain or [],
            status="pending",
            current_approval_level=0
        )
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request

    def get_request(self, request_id: int) -> Optional[Request]:
        return self.session.get(Request, request_id)

    def get_request_by_uuid(self, uuid: str) -> Optional[Request]:
        return self.session.query(Request).filter(Request.uuid == uuid).first()

    def list_requests(
        self,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Request]:
        query = self.session.query(Request)
        
        if organization_id:
            query = query.filter(Request.organization_id == organization_id)
        if status:
            query = query.filter(Request.status == status)
        if type:
            query = query.filter(Request.type == type)
        if user_id:
            query = query.filter(Request.user_id == user_id)
        
        return query.order_by(Request.created_at.desc()).all()

    def approve(
        self,
        request_id: int,
        approver_id: int,
        comment: Optional[str] = None
    ) -> Optional[Request]:
        request = self.session.get(Request, request_id)
        if not request:
            return None
        
        if request.status != "pending":
            logger.warning(f"Request {request_id} is not pending, current status: {request.status}")
            return request
        
        action = ApprovalAction(
            request_id=request_id,
            approver_id=approver_id,
            level=request.current_approval_level + 1,
            action="approve",
            comment=comment
        )
        self.session.add(action)
        
        if request.approval_chain:
            next_level = request.current_approval_level + 1
            if next_level < len(request.approval_chain):
                request.current_approval_level = next_level
                request.status = "pending"
            else:
                request.status = "approved"
        else:
            request.status = "approved"
        
        request.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(request)
        return request

    def reject(
        self,
        request_id: int,
        approver_id: int,
        comment: Optional[str] = None
    ) -> Optional[Request]:
        request = self.session.get(Request, request_id)
        if not request:
            return None
        
        action = ApprovalAction(
            request_id=request_id,
            approver_id=approver_id,
            level=request.current_approval_level + 1,
            action="reject",
            comment=comment
        )
        self.session.add(action)
        
        request.status = "rejected"
        request.result = comment
        request.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(request)
        return request

    def execute(self, request_id: int) -> Optional[Request]:
        request = self.session.get(Request, request_id)
        if not request:
            return None
        
        if request.status != "approved":
            logger.warning(f"Request {request_id} is not approved, cannot execute")
            return None
        
        request.status = "executing"
        request.executed_at = datetime.utcnow()
        request.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(request)
        return request

    def complete(self, request_id: int, success: bool = True, result: Optional[str] = None) -> Optional[Request]:
        request = self.session.get(Request, request_id)
        if not request:
            return None
        
        request.status = "completed" if success else "failed"
        request.result = result
        request.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(request)
        return request

    def get_pending_approvals(self, user_id: int) -> List[Request]:
        requests = self.session.query(Request).filter(
            Request.status == "pending"
        ).all()
        
        pending = []
        for req in requests:
            if req.approval_chain and len(req.approval_chain) > req.current_approval_level:
                next_approver_id = req.approval_chain[req.current_approval_level]
                if next_approver_id == user_id:
                    pending.append(req)
            elif not req.approval_chain:
                pending.append(req)
        
        return pending

    def get_user_requests(self, user_id: int) -> List[Request]:
        return self.session.query(Request).filter(
            Request.user_id == user_id
        ).order_by(Request.created_at.desc()).all()


class ApprovalService:
    def __init__(self, session: Session):
        self.session = session

    def auto_approve_if_quota_available(self, request: Request) -> bool:
        if request.type != "vm_create":
            return False
        
        org_service = OrganizationService(self.session)
        details = request.details
        
        quota_ok, msg = org_service.check_quota(
            org_id=request.organization_id,
            cpu=details.get("cpu", 0),
            memory_gb=details.get("memory_gb", 0),
            storage_tb=details.get("storage_gb", 0) / 1024 if details.get("storage_gb") else 0
        )
        
        if quota_ok:
            request.status = "approved"
            request.result = "Auto-approved: quota available"
            self.session.commit()
            return True
        
        return False

    def get_approval_history(self, request_id: int) -> List[ApprovalAction]:
        return self.session.query(ApprovalAction).filter(
            ApprovalAction.request_id == request_id
        ).order_by(ApprovalAction.created_at).all()
