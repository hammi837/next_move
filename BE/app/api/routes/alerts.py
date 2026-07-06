"""
Alert CRUD + manual price-check routes (sync stack).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import auth_service
from app.services.alert_service import alert_service

router   = APIRouter()
security = HTTPBearer(auto_error=False)


def _user(credentials: HTTPAuthCredentials = Depends(security),
          db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    u = auth_service.get_user_from_token(db, credentials.credentials)
    if not u:
        raise HTTPException(401, "Invalid token")
    return u


def _alert_dict(a) -> dict:
    return {
        "id":              a.id,
        "symbol":          a.symbol,
        "alert_type":      a.alert_type,
        "condition":       a.condition,
        "threshold_value": a.threshold_value,
        "note":            a.note,
        "is_active":       bool(a.is_active),
        "is_triggered":    bool(a.is_triggered),
        "triggered_at":    a.triggered_at.isoformat() if a.triggered_at else None,
        "triggered_price": a.triggered_price,
        "created_at":      a.created_at.isoformat() if a.created_at else None,
    }


# ── List ──────────────────────────────────────────────────────────────────

@router.get("")
def list_alerts(active_only: bool = False,
                user=Depends(_user), db: Session = Depends(get_db)):
    return [_alert_dict(a) for a in
            alert_service.list_for_user(db, user.id, active_only)]


# ── Create ────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_alert(payload: dict,
                 user=Depends(_user), db: Session = Depends(get_db)):
    """
    Body: { symbol, condition, threshold_value, alert_type?, note? }
    condition: above | below | crosses
    """
    a = alert_service.create(
        db,
        user_id         = user.id,
        symbol          = payload.get("symbol", ""),
        condition       = payload.get("condition", "above"),
        threshold_value = float(payload.get("threshold_value", 0)),
        alert_type      = payload.get("alert_type", "price"),
        note            = payload.get("note", ""),
    )
    return _alert_dict(a)


# ── Update ────────────────────────────────────────────────────────────────

@router.put("/{alert_id}")
def update_alert(alert_id: int, payload: dict,
                 user=Depends(_user), db: Session = Depends(get_db)):
    a = alert_service.update(db, alert_id, user.id, **payload)
    if not a:
        raise HTTPException(404, "Alert not found")
    return _alert_dict(a)


# ── Delete ────────────────────────────────────────────────────────────────

@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: int,
                 user=Depends(_user), db: Session = Depends(get_db)):
    if not alert_service.delete(db, alert_id, user.id):
        raise HTTPException(404, "Alert not found")


# ── Check (manual trigger test) ───────────────────────────────────────────

@router.post("/check/{symbol}")
def check_alerts(symbol: str, payload: dict,
                 db: Session = Depends(get_db)):
    """Trigger check for a symbol at a given price. Used by background tasks."""
    price     = float(payload.get("price", 0))
    triggered = alert_service.check_and_trigger(db, symbol, price)
    return {"triggered": triggered, "count": len(triggered)}
