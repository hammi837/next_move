"""
Authentication route module.

Provides registration, login, token refresh, and user-profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db_session
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Create a new user account."""
    from app.models.user import User

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=dict,
    summary="Login and receive JWT",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Authenticate user and return an access token."""
    from app.models.user import User

    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(
    current_user=Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
)
def refresh_token(
    current_user=Depends(get_current_user),
) -> dict:
    """Issue a fresh access token for the authenticated user."""
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
