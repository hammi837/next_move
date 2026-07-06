"""
Core security utilities — real bcrypt + python-jose JWT.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fallback so the app doesn't crash if SECRET_KEY wasn't added to .env yet
_SECRET  = getattr(settings, "SECRET_KEY", "change-me-in-production-32chars+")
_ALG     = getattr(settings, "ALGORITHM",  "HS256")
_EXPIRES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)   # 24 h default


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: Dict[str, Any],
                        expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.utcnow() + (expires_delta or timedelta(minutes=_EXPIRES))
    payload.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(payload, _SECRET, algorithm=_ALG)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALG])
    except JWTError:
        return None
