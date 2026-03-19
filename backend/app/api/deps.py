from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.models.user import User
from app.models.session import Session as SessionModel
from datetime import datetime

SESSION_COOKIE_NAME = "session_id"


def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    
    db_session = session.query(SessionModel).filter(
        SessionModel.token == token,
        SessionModel.expires_at != None,
        SessionModel.expires_at > datetime.utcnow()
    ).first()
    
    if not db_session:
        return None
    
    user = session.query(User).filter(User.id == db_session.user_id).first()
    return user


def require_current_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user


def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(require_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
