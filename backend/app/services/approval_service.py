import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.approval import ApprovalTemplate, ApprovalRequest, ApprovalRecord
from app.models.user import User

logger = logging.getLogger(__name__)


class ApprovalService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_templates(self, request_type: str = None) -> List[ApprovalTemplate]:
        query = self.session.query(ApprovalTemplate)
        if request_type:
            query = query.filter(ApprovalTemplate.request_type == request_type)
        return query.all()
    
    def get_template(self, template_id: int) -> Optional[ApprovalTemplate]:
        return self.session.query(ApprovalTemplate).filter(ApprovalTemplate.id == template_id).first()
    
    def create_template(
        self,
        name: str,
        request_type: str,
        steps: List[Dict[str, Any]],
        is_auto_approve: bool = False
    ) -> ApprovalTemplate:
        template = ApprovalTemplate(
            name=name,
            request_type=request_type,
            steps=json.dumps(steps),
            is_auto_approve=is_auto_approve
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template
    
    def create_request(
        self,
        request_type: str,
        tenant_id: int,
        applicant_id: int,
        resource_type: str,
        resource_id: str,
        detail: Dict[str, Any],
        template_id: int = None
    ) -> ApprovalRequest:
        template = None
        if template_id:
            template = self.get_template(template_id)
        
        if not template:
            templates = self.get_templates(request_type)
            if templates:
                template = templates[0]
        
        if template and template.is_auto_approve:
            status = "approved"
        else:
            status = "pending"
        
        request = ApprovalRequest(
            request_type=request_type,
            tenant_id=tenant_id,
            applicant_id=applicant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=json.dumps(detail),
            status=status,
            template_id=template.id if template else None,
            current_step=0
        )
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request
    
    def get_request(self, request_id: int) -> Optional[ApprovalRequest]:
        return self.session.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    
    def get_requests(
        self,
        tenant_id: int = None,
        status: str = None,
        request_type: str = None,
        limit: int = 50
    ) -> List[ApprovalRequest]:
        query = self.session.query(ApprovalRequest)
        
        if tenant_id:
            query = query.filter(ApprovalRequest.tenant_id == tenant_id)
        if status:
            query = query.filter(ApprovalRequest.status == status)
        if request_type:
            query = query.filter(ApprovalRequest.request_type == request_type)
        
        return query.order_by(ApprovalRequest.created_at.desc()).limit(limit).all()
    
    def get_pending_requests(self, approver_id: int, tenant_ids: List[int]) -> List[Dict[str, Any]]:
        requests = self.session.query(ApprovalRequest).filter(
            ApprovalRequest.tenant_id.in_(tenant_ids),
            ApprovalRequest.status == "pending"
        ).all()
        
        result = []
        for req in requests:
            if self._can_approve(req, approver_id):
                result.append(self._request_to_dict(req))
        
        return result
    
    def _can_approve(self, request: ApprovalRequest, approver_id: int) -> bool:
        if not request.template_id:
            return True
        
        template = self.get_template(request.template_id)
        if not template:
            return True
        
        steps = json.loads(template.steps)
        if request.current_step >= len(steps):
            return False
        
        current_step_config = steps[request.current_step]
        
        if current_step_config.get("type") == "auto":
            return False
        
        if current_step_config.get("type") == "user":
            approver = current_step_config.get("approver")
            if approver == "applicant":
                return request.applicant_id != approver_id
            return True
        
        return True
    
    def approve(self, request_id: int, approver_id: int, comment: str = None) -> Dict[str, Any]:
        request = self.get_request(request_id)
        if not request:
            return {"success": False, "message": "Request not found"}
        
        if request.status != "pending":
            return {"success": False, "message": "Request is not pending"}
        
        record = ApprovalRecord(
            request_id=request_id,
            step_order=request.current_step,
            approver_id=approver_id,
            action="approve",
            comment=comment
        )
        self.session.add(record)
        
        template = None
        if request.template_id:
            template = self.get_template(request.template_id)
        
        if template:
            steps = json.loads(template.steps)
            request.current_step += 1
            
            if request.current_step >= len(steps):
                request.status = "approved"
            else:
                next_step = steps[request.current_step]
                if next_step.get("type") == "auto":
                    return self._process_auto_step(request, next_step)
        else:
            request.status = "approved"
        
        request.updated_at = datetime.utcnow()
        self.session.commit()
        
        return {
            "success": True,
            "message": "Request approved",
            "status": request.status,
            "request_id": request_id
        }
    
    def reject(self, request_id: int, approver_id: int, comment: str = None) -> Dict[str, Any]:
        request = self.get_request(request_id)
        if not request:
            return {"success": False, "message": "Request not found"}
        
        if request.status != "pending":
            return {"success": False, "message": "Request is not pending"}
        
        record = ApprovalRecord(
            request_id=request_id,
            step_order=request.current_step,
            approver_id=approver_id,
            action="reject",
            comment=comment
        )
        self.session.add(record)
        
        request.status = "rejected"
        request.updated_at = datetime.utcnow()
        self.session.commit()
        
        return {
            "success": True,
            "message": "Request rejected",
            "status": "rejected",
            "request_id": request_id
        }
    
    def _process_auto_step(self, request: ApprovalRequest, step_config: Dict[str, Any]) -> Dict[str, Any]:
        condition = step_config.get("condition")
        if not condition:
            request.status = "approved"
            request.updated_at = datetime.utcnow()
            self.session.commit()
            return {"success": True, "message": "Auto-approved", "status": "approved", "request_id": request.id}
        
        detail = json.loads(request.detail)
        
        if self._evaluate_condition(condition, detail):
            request.status = "approved"
        else:
            request.current_step += 1
            if request.current_step >= len(json.loads(self.get_template(request.template_id).steps)):
                request.status = "approved"
        
        request.updated_at = datetime.utcnow()
        self.session.commit()
        
        return {"success": True, "message": "Processed", "status": request.status, "request_id": request.id}
    
    def _evaluate_condition(self, condition: str, detail: Dict[str, Any]) -> bool:
        try:
            for key, value in detail.items():
                condition = condition.replace(key, str(value))
            return eval(condition)
        except:
            return False
    
    def _request_to_dict(self, request: ApprovalRequest) -> Dict[str, Any]:
        return {
            "id": request.id,
            "request_type": request.request_type,
            "tenant_id": request.tenant_id,
            "applicant_id": request.applicant_id,
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "detail": json.loads(request.detail) if request.detail else {},
            "status": request.status,
            "template_id": request.template_id,
            "current_step": request.current_step,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "updated_at": request.updated_at.isoformat() if request.updated_at else None
        }
    
    def get_request_history(self, request_id: int) -> List[Dict[str, Any]]:
        records = self.session.query(ApprovalRecord, User).join(
            User, ApprovalRecord.approver_id == User.id
        ).filter(ApprovalRecord.request_id == request_id).order_by(
            ApprovalRecord.created_at.asc()
        ).all()
        
        return [
            {
                "id": record.id,
                "step_order": record.step_order,
                "approver_id": record.approver_id,
                "approver_name": user.username,
                "action": record.action,
                "comment": record.comment,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
            for record, user in records
        ]
