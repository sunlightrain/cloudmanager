import pytest
from sqlmodel import SQLModel
from app.core.database import engine


@pytest.fixture(autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
