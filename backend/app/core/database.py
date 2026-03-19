from typing import Optional
from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
    max_overflow=10
)


def init_db():
    from app.models.user import User
    from app.models.task import Task
    from app.models.operation_log import OperationLog
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
