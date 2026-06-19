"""
Core security utilities for authentication.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Placeholders for actual security logic

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a mock JWT token."""
    return "mock_jwt_token_for_" + str(data.get("sub", "unknown"))

def hash_password(password: str) -> str:
    """Hash a password (mock)."""
    return "hashed_" + password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password (mock)."""
    return hashed_password == "hashed_" + plain_password

def verify_token(token: str) -> Dict[str, Any]:
    """Verify a mock JWT token."""
    return {"sub": "mock_user_id"}
