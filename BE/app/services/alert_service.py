"""
Alert service.

Business logic for creating, checking, and triggering price alerts.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class AlertService:
    """Manages lifecycle of user price alerts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_alert(
        self,
        user_id: int,
        symbol: str,
        condition: str,
        threshold: float,
    ) -> dict[str, Any]:
        """Create a new price alert and persist it."""
        from app.models.alert import Alert, AlertCondition

        alert = Alert(
            user_id=user_id,
            symbol=symbol.upper(),
            condition=AlertCondition(condition),
            threshold=threshold,
            is_active=True,
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return {
            "id": alert.id,
            "symbol": alert.symbol,
            "condition": alert.condition.value,
            "threshold": alert.threshold,
            "is_active": alert.is_active,
        }

    async def check_alerts(
        self,
        symbol: str,
        current_price: float,
    ) -> list[dict[str, Any]]:
        """
        Check all active alerts for *symbol* against *current_price*.

        Returns a list of triggered alert details.
        """
        from app.models.alert import Alert, AlertCondition

        result = await self.db.execute(
            select(Alert).where(
                Alert.symbol == symbol.upper(),
                Alert.is_active == True,  # noqa: E712
            )
        )
        alerts = result.scalars().all()
        triggered: list[dict[str, Any]] = []

        for alert in alerts:
            should_trigger = False
            if alert.condition == AlertCondition.ABOVE and current_price >= alert.threshold:
                should_trigger = True
            elif alert.condition == AlertCondition.BELOW and current_price <= alert.threshold:
                should_trigger = True
            elif alert.condition == AlertCondition.PERCENT_CHANGE:
                # percent_change alerts need a reference price – simplified here
                should_trigger = False

            if should_trigger:
                triggered_info = await self.trigger_alert(alert.id)
                triggered.append(triggered_info)

        return triggered

    async def trigger_alert(self, alert_id: int) -> dict[str, Any]:
        """Mark an alert as triggered and deactivate it."""
        from app.models.alert import Alert

        now = datetime.utcnow()
        await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(is_active=False, triggered_at=now)
        )
        return {
            "alert_id": alert_id,
            "triggered_at": now.isoformat(),
            "status": "triggered",
        }
