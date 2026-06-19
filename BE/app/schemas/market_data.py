"""
MarketData Pydantic schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketDataCreate(BaseModel):
    """Schema for inserting new market data."""

    symbol: str = Field(..., max_length=20)
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = 0
    asset_type: str = Field("stock", pattern="^(stock|gold|commodity)$")


class MarketDataUpdate(BaseModel):
    """Schema for updating market data records."""

    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class MarketDataResponse(BaseModel):
    """Schema for market data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = 0
    asset_type: str
    created_at: datetime
