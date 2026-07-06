from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum, Index
from datetime import datetime
import enum
from app.db.database import Base


# ── Enums ────────────────────────────────────────────────────────────────

class MarketType(str, enum.Enum):
    GOLD = "gold"
    STOCK = "stock"
    COMMODITY = "commodity"


class TrendDirection(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class SignalType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# ── Price History ────────────────────────────────────────────────────────

class PriceHistory(Base):
    """Historical price data for all markets."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    market_type = Column(Enum(MarketType), nullable=False)

    # OHLCV
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)

    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_market_type_timestamp", "market_type", "timestamp"),
    )


# ── Technical Indicators ─────────────────────────────────────────────────

class TechnicalIndicators(Base):
    """Calculated technical indicators."""
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)

    # Moving Averages
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)

    # Momentum
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)

    # Volatility
    bollinger_upper = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)

    # Volume
    volume_sma = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ti_symbol_timestamp", "symbol", "timestamp"),
    )


# ── Market Signals ───────────────────────────────────────────────────────

class MarketSignal(Base):
    """Generated trading signals."""
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    strength = Column(Float, nullable=False)  # 0.0 to 1.0

    indicators_used = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    reason = Column(JSON, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_signal_symbol_timestamp", "symbol", "timestamp"),
    )


# ── Market Stats ─────────────────────────────────────────────────────────

class MarketStats(Base):
    """Daily / aggregated market statistics."""
    __tablename__ = "market_stats"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)

    date = Column(DateTime, index=True, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Float)

    change_percent = Column(Float, nullable=True)
    trend = Column(Enum(TrendDirection), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_stats_symbol_date", "symbol", "date"),
    )


# ── Market Metadata ──────────────────────────────────────────────────────

class MarketMetadata(Base):
    """Market information and metadata."""
    __tablename__ = "market_metadata"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    market_type = Column(Enum(MarketType), nullable=False)

    name = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)

    last_price = Column(Float, nullable=True)
    last_update = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Data Sync Log ────────────────────────────────────────────────────────

class DataSyncLog(Base):
    """Log of data collection and sync operations."""
    __tablename__ = "data_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    operation = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)

    record_count = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ── Phase 4 Models ────────────────────────────────────────────────────────
# Added here so init_db() picks them up via app/db/database.py Base.

class UserRole(str, enum.Enum):
    ADMIN   = "admin"
    PREMIUM = "premium"
    FREE    = "free"


class AppUser(Base):
    """User accounts (sync stack version)."""
    __tablename__ = "app_users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, index=True, nullable=False)
    email           = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(200), nullable=True)
    role            = Column(Enum(UserRole), default=UserRole.FREE)
    is_active       = Column(Integer, default=1)
    preferences     = Column(JSON, default={})
    created_at      = Column(DateTime, default=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)


class Portfolio(Base):
    """User portfolios."""
    __tablename__ = "portfolios"

    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, index=True, nullable=False)
    name               = Column(String(100), nullable=False)
    description        = Column(String(500), nullable=True)
    initial_investment = Column(Float, default=0.0)
    current_value      = Column(Float, default=0.0)
    risk_level         = Column(String(20), default="medium")
    is_public          = Column(Integer, default=0)
    created_at         = Column(DateTime, default=datetime.utcnow)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_portfolio_user", "user_id"),)


class Position(Base):
    """Holdings inside a portfolio."""
    __tablename__ = "positions"

    id                  = Column(Integer, primary_key=True, index=True)
    portfolio_id        = Column(Integer, index=True, nullable=False)
    symbol              = Column(String(20), nullable=False)
    quantity            = Column(Float, nullable=False)
    entry_price         = Column(Float, nullable=False)
    entry_date          = Column(DateTime, default=datetime.utcnow)
    current_price       = Column(Float, nullable=True)
    current_value       = Column(Float, nullable=True)
    profit_loss         = Column(Float, nullable=True)
    profit_loss_percent = Column(Float, nullable=True)
    stop_loss           = Column(Float, nullable=True)
    take_profit         = Column(Float, nullable=True)
    status              = Column(String(20), default="open")
    closed_date         = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_position_portfolio", "portfolio_id"),)


class UserAlert(Base):
    """User-defined price & signal alerts (sync stack)."""
    __tablename__ = "user_alerts"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, index=True, nullable=False)
    symbol          = Column(String(20), nullable=False, index=True)
    alert_type      = Column(String(50), default="price")   # price, signal, rsi
    condition       = Column(String(50), nullable=False)    # above, below, crosses
    threshold_value = Column(Float, nullable=True)
    note            = Column(String(255), nullable=True)
    is_active       = Column(Integer, default=1)
    is_triggered    = Column(Integer, default=0)
    triggered_at    = Column(DateTime, nullable=True)
    triggered_price = Column(Float, nullable=True)
    notify_email    = Column(Integer, default=1)
    created_at      = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_alert_user_symbol", "user_id", "symbol"),
        Index("idx_alert_active",      "is_active", "is_triggered"),
    )


class WatchList(Base):
    """User watch lists."""
    __tablename__ = "watch_lists"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, index=True, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    symbols     = Column(JSON, default=[])
    is_public   = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
