from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Field, create_engine, Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None)
    password_hash: str = Field()
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
