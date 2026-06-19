"""
User Pydantic schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
