from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

SESSION_COOKIE_NAME = "session_id"


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
    
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=user.username,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax"
    )
    
    return ResponseModel(
        data={
            "user_id": user.id,
            "username": user.username
        }
    )


@router.post("/logout", response_model=ResponseModel)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return ResponseModel(message="Logout successful")


@router.get("/me", response_model=ResponseModel)
def get_current_user_info(request: Request, session: Session = Depends(get_session)):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = session.query(User).filter(User.username == session_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return ResponseModel(
        data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    )
