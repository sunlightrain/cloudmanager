import pytest
from app.models.session import Session
from datetime import datetime, timedelta


def test_session_creation():
    session = Session(
        token="test_token_12345",
        user_id=1,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    assert session.token == "test_token_12345"
    assert session.user_id == 1
    assert session.expires_at > datetime.utcnow()


def test_session_default_values():
    session = Session(token="test_token", user_id=1)
    
    assert session.id is None
    assert session.created_at is not None
    assert session.expires_at is None
