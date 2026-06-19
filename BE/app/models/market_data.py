"""
MarketData ORM model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssetType(str, enum.Enum):
    """Supported asset categories."""

    STOCK = "stock"
    GOLD = "gold"
    COMMODITY = "commodity"


class MarketData(Base):
    """Historical and real-time OHLCV market data."""

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=True, default=0)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType), nullable=False, default=AssetType.STOCK
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MarketData {self.symbol} @ {self.timestamp}>"
