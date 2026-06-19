"""
Common FastAPI dependencies shared across route modules.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Database session dependency ─────────────────────────────────────────────
async def get_db_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Alias dependency – returns the active async DB session."""
    return session


# ── Current user dependency ─────────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Decode the JWT and return the current user payload.

    Raises 401 if the token is invalid or the user cannot be found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # In a full implementation you would query the User model here.
    # For now return the decoded payload.
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# ── Pagination parameters ──────────────────────────────────────────────────
class PaginationParams:
    """Reusable pagination query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
