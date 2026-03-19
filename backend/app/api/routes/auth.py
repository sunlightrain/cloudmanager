from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.security import verify_password
from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.schemas.common import ResponseModel
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRE_HOURS = 24


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("/login", response_model=ResponseModel)
def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    session: Session = Depends(get_session)
):
    user = session.query(User).filter(User.username == login_data.username).first()
    
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    token = create_session_token()
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    
    db_session = SessionModel(
        token=token,
        user_id=user.id,
        expires_at=expires_at
    )
    session.add(db_session)
    session.commit()
    
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=SESSION_EXPIRE_HOURS * 60 * 60,
        samesite="lax",
        secure=True
    )
    
    return ResponseModel(
        data={
            "user_id": user.id,
            "username": user.username
        }
    )


@router.post("/logout", response_model=ResponseModel)
def logout(request: Request, response: Response, session: Session = Depends(get_session)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session.query(SessionModel).filter(SessionModel.token == token).delete()
        session.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
    return ResponseModel(message="Logout successful")


@router.get("/me", response_model=ResponseModel)
def get_current_user_info(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    db_session = session.query(SessionModel).filter(
        SessionModel.token == token,
        SessionModel.expires_at != None,
        SessionModel.expires_at > datetime.utcnow()
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    user = session.query(User).filter(User.id == db_session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return ResponseModel(
        data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )
