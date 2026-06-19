"""
Alert Pydantic schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    """Schema for creating a new alert."""

    symbol: str = Field(..., max_length=20)
    condition: str = Field(..., pattern="^(above|below|percent_change)$")
    threshold: float


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""

    symbol: Optional[str] = Field(None, max_length=20)
    condition: Optional[str] = Field(None, pattern="^(above|below|percent_change)$")
    threshold: Optional[float] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Schema for alert data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    symbol: str
    condition: str
    threshold: float
    is_active: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime
