"""
Alert management service — CRUD + price-check triggering.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

from sqlalchemy.orm import Session
from app.db.models import UserAlert

logger = logging.getLogger(__name__)


class AlertService:

    # ── CRUD ──────────────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, user_id: int, symbol: str,
               condition: str, threshold_value: float,
               alert_type: str = "price",
               note: str = "") -> UserAlert:
        a = UserAlert(
            user_id         = user_id,
            symbol          = symbol.upper(),
            alert_type      = alert_type,
            condition       = condition.lower(),
            threshold_value = threshold_value,
            note            = note,
        )
        db.add(a)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def list_for_user(db: Session, user_id: int,
                      active_only: bool = False) -> List[UserAlert]:
        q = db.query(UserAlert).filter(UserAlert.user_id == user_id)
        if active_only:
            q = q.filter(UserAlert.is_active == 1)
        return q.order_by(UserAlert.created_at.desc()).all()

    @staticmethod
    def update(db: Session, alert_id: int, user_id: int,
               **kwargs) -> Optional[UserAlert]:
        a = db.query(UserAlert).filter(
            UserAlert.id == alert_id,
            UserAlert.user_id == user_id,
        ).first()
        if not a:
            return None
        for k, v in kwargs.items():
            if hasattr(a, k):
                setattr(a, k, v)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def delete(db: Session, alert_id: int, user_id: int) -> bool:
        a = db.query(UserAlert).filter(
            UserAlert.id == alert_id,
            UserAlert.user_id == user_id,
        ).first()
        if not a:
            return False
        db.delete(a)
        db.commit()
        return True

    # ── Price checking ────────────────────────────────────────────────────

    @staticmethod
    def check_and_trigger(db: Session, symbol: str,
                           current_price: float) -> List[Dict]:
        """
        Check all active un-triggered alerts for `symbol`.
        Returns list of triggered alert dicts.
        """
        alerts = db.query(UserAlert).filter(
            UserAlert.symbol       == symbol.upper(),
            UserAlert.is_active    == 1,
            UserAlert.is_triggered == 0,
        ).all()

        triggered = []
        for alert in alerts:
            should_fire = False
            thr = alert.threshold_value

            if alert.condition == "above"  and current_price >  thr:
                should_fire = True
            elif alert.condition == "below" and current_price <  thr:
                should_fire = True
            elif alert.condition == "crosses":
                should_fire = abs(current_price - thr) / thr < 0.005

            if should_fire:
                alert.is_triggered    = 1
                alert.triggered_at    = datetime.utcnow()
                alert.triggered_price = current_price
                db.commit()
                triggered.append({
                    "alert_id":      alert.id,
                    "user_id":       alert.user_id,
                    "symbol":        alert.symbol,
                    "condition":     alert.condition,
                    "threshold":     thr,
                    "current_price": current_price,
                    "message":       f"{alert.symbol} {alert.condition} ${thr:.2f} — now ${current_price:.2f}",
                })
                logger.info(f"🔔 Alert {alert.id} triggered for user {alert.user_id}")

        return triggered


alert_service = AlertService()
