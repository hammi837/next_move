"""
Prediction Pydantic schemas.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PredictionCreate(BaseModel):
    """Schema for creating a new prediction record."""

    symbol: str = Field(..., max_length=20)
    predicted_price: float = Field(..., gt=0)
    confidence: float = Field(..., ge=0, le=1)
    model_used: str = Field("ensemble", max_length=50)
    prediction_date: date
    target_date: date
    actual_price: Optional[float] = None


class PredictionUpdate(BaseModel):
    """Schema for updating a prediction (e.g. filling actual_price)."""

    actual_price: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class PredictionResponse(BaseModel):
    """Schema for prediction data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    predicted_price: float
    confidence: float
    model_used: str
    prediction_date: date
    target_date: date
    actual_price: Optional[float] = None
    created_at: datetime
