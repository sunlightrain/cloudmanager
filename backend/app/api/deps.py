from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.models.user import User

SESSION_COOKIE_NAME = "session_id"


def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    
    from app.core.security import verify_password
    
    user = session.query(User).filter(User.username == session_id).first()
    return user


def require_current_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user
