"""
Alert ORM model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlertCondition(str, enum.Enum):
    """Supported alert trigger conditions."""

    ABOVE = "above"
    BELOW = "below"
    PERCENT_CHANGE = "percent_change"


class Alert(Base):
    """User-defined price alert."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    condition: Mapped[AlertCondition] = mapped_column(
        Enum(AlertCondition), nullable=False
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="alerts")

    def __repr__(self) -> str:
        return (
            f"<Alert {self.symbol} {self.condition.value} {self.threshold} "
            f"active={self.is_active}>"
        )
