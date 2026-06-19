from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────────

class MarketTypeEnum(str, Enum):
    GOLD = "gold"
    STOCK = "stock"
    COMMODITY = "commodity"


class TrendDirectionEnum(str, Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class SignalTypeEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# ── Price History ────────────────────────────────────────────────────────

class PriceHistoryBase(BaseModel):
    symbol: str
    market_type: MarketTypeEnum
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float
    volume: Optional[float] = None
    timestamp: datetime


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistoryResponse(PriceHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Technical Indicators ─────────────────────────────────────────────────

class TechnicalIndicatorsBase(BaseModel):
    symbol: str
    timestamp: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None


class TechnicalIndicatorsResponse(TechnicalIndicatorsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Market Signals ───────────────────────────────────────────────────────

class MarketSignalBase(BaseModel):
    symbol: str
    signal_type: SignalTypeEnum
    strength: float = Field(ge=0.0, le=1.0)
    indicators_used: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class MarketSignalResponse(MarketSignalBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Market Stats ─────────────────────────────────────────────────────────

class MarketStatsBase(BaseModel):
    symbol: str
    date: datetime
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[float] = None
    change_percent: Optional[float] = None
    trend: Optional[TrendDirectionEnum] = None


class MarketStatsResponse(MarketStatsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Market Metadata ──────────────────────────────────────────────────────

class MarketMetadataBase(BaseModel):
    symbol: str
    market_type: MarketTypeEnum
    name: Optional[str] = None
    description: Optional[str] = None


class MarketMetadataCreate(MarketMetadataBase):
    pass


class MarketMetadataResponse(MarketMetadataBase):
    id: int
    last_price: Optional[float] = None
    last_update: Optional[datetime] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Combined Responses ───────────────────────────────────────────────────

class MarketDataResponse(BaseModel):
    """Combined market data response."""
    symbol: str
    current_price: float
    latest_prices: List[PriceHistoryResponse]
    indicators: Optional[TechnicalIndicatorsResponse] = None
    signal: Optional[MarketSignalResponse] = None
    stats: Optional[MarketStatsResponse] = None


class DashboardResponse(BaseModel):
    """Dashboard summary data."""
    timestamp: datetime
    markets: List[MarketDataResponse]
    overall_trend: TrendDirectionEnum
