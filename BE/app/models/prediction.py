"""
Prediction ORM model.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Prediction(Base):
    """ML-generated price prediction."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_used: Mapped[str] = mapped_column(String(50), nullable=False, default="ensemble")
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction {self.symbol} predicted={self.predicted_price} "
            f"confidence={self.confidence:.2f}>"
        )
