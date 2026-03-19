import pytest
from app.models.user import User


def test_password_hashing():
    password = "test_password123"
    hashed = User.hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0


def test_password_verification():
    password = "test_password123"
    user = User(username="testuser", password_hash=User.hash_password(password))
    
    assert user.verify_password(password) is True
    assert user.verify_password("wrong_password") is False


def test_user_creation():
    user = User(username="admin", email="admin@example.com", role="admin")
    
    assert user.username == "admin"
    assert user.email == "admin@example.com"
    assert user.role == "admin"
    assert user.is_active is True
