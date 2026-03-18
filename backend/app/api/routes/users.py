from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("", response_model=ResponseModel)
def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    users = session.query(User).offset((page - 1) * page_size).limit(page_size).all()
    total = session.query(User).count()
    
    items = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": getattr(u, 'role', 'user'),
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]
    
    return ResponseModel(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/{user_id}", response_model=ResponseModel)
def get_user(
    user_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ResponseModel(data={
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": getattr(user, 'role', 'user'),
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


@router.post("", response_model=ResponseModel)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    existing = session.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        email=user_data.email,
        is_active=True
    )
    if hasattr(User, 'role'):
        user.role = user_data.role
    
    session.add(user)
    session.commit()
    
    return ResponseModel(message="User created successfully", data={"id": user.id})


@router.put("/{user_id}", response_model=ResponseModel)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
    if user_data.is_active is not None and current_user.role == "admin":
        user.is_active = user_data.is_active
    if user_data.role is not None and current_user.role == "admin":
        if hasattr(user, 'role'):
            user.role = user_data.role
    
    session.commit()
    
    return ResponseModel(message="User updated successfully")


@router.delete("/{user_id}", response_model=ResponseModel)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session.delete(user)
    session.commit()
    
    return ResponseModel(message="User deleted successfully")
