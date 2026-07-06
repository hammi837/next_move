"""
Portfolio & position management routes (sync stack).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import auth_service
from app.services.portfolio_service import portfolio_service

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


def _pf_dict(p) -> dict:
    return {
        "id":                 p.id,
        "name":               p.name,
        "description":        p.description,
        "initial_investment": p.initial_investment,
        "current_value":      p.current_value,
        "risk_level":         p.risk_level,
        "is_public":          bool(p.is_public),
        "created_at":         p.created_at.isoformat() if p.created_at else None,
    }


# ── Portfolios ────────────────────────────────────────────────────────────

@router.get("")
def list_portfolios(user=Depends(_user), db: Session = Depends(get_db)):
    return [_pf_dict(p) for p in
            portfolio_service.list_for_user(db, user.id)]


@router.post("", status_code=201)
def create_portfolio(payload: dict,
                     user=Depends(_user), db: Session = Depends(get_db)):
    """Body: { name, initial_investment?, description?, risk_level? }"""
    p = portfolio_service.create(
        db,
        user_id            = user.id,
        name               = payload.get("name", "My Portfolio"),
        initial_investment = float(payload.get("initial_investment", 0)),
        description        = payload.get("description", ""),
        risk_level         = payload.get("risk_level", "medium"),
    )
    return _pf_dict(p)


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int,
                     user=Depends(_user), db: Session = Depends(get_db)):
    if not portfolio_service.delete(db, portfolio_id, user.id):
        raise HTTPException(404, "Portfolio not found")


# ── Metrics ───────────────────────────────────────────────────────────────

@router.get("/{portfolio_id}/metrics")
def get_metrics(portfolio_id: int,
                user=Depends(_user), db: Session = Depends(get_db)):
    pf = portfolio_service.get(db, portfolio_id, user.id)
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    # Pull latest prices for open positions from market metadata
    from app.db.models import MarketMetadata
    symbols = [pos["symbol"] for pos in
               portfolio_service.metrics(db, portfolio_id)["positions"]]
    prices  = {}
    if symbols:
        rows = db.query(MarketMetadata).filter(
            MarketMetadata.symbol.in_(symbols)
        ).all()
        prices = {r.symbol: r.last_price for r in rows if r.last_price}
        if prices:
            portfolio_service.update_prices(db, portfolio_id, prices)

    return portfolio_service.metrics(db, portfolio_id)


# ── Positions ─────────────────────────────────────────────────────────────

@router.post("/{portfolio_id}/positions", status_code=201)
def add_position(portfolio_id: int, payload: dict,
                 user=Depends(_user), db: Session = Depends(get_db)):
    """Body: { symbol, quantity, entry_price, stop_loss?, take_profit? }"""
    pf = portfolio_service.get(db, portfolio_id, user.id)
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    pos = portfolio_service.add_position(
        db,
        portfolio_id = portfolio_id,
        symbol       = payload.get("symbol", ""),
        quantity     = float(payload.get("quantity", 1)),
        entry_price  = float(payload.get("entry_price", 0)),
        stop_loss    = payload.get("stop_loss"),
        take_profit  = payload.get("take_profit"),
    )
    return {
        "id":          pos.id,
        "symbol":      pos.symbol,
        "quantity":    pos.quantity,
        "entry_price": pos.entry_price,
        "status":      pos.status,
    }


@router.put("/{portfolio_id}/positions/{position_id}/close")
def close_position(portfolio_id: int, position_id: int,
                   payload: dict,
                   user=Depends(_user), db: Session = Depends(get_db)):
    pf = portfolio_service.get(db, portfolio_id, user.id)
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    exit_price = float(payload.get("exit_price", 0))
    pos        = portfolio_service.close_position(db, position_id, exit_price)
    if not pos:
        raise HTTPException(404, "Position not found or already closed")

    return {
        "id":               pos.id,
        "symbol":           pos.symbol,
        "status":           pos.status,
        "exit_price":       pos.current_price,
        "profit_loss":      round(pos.profit_loss or 0, 2),
        "profit_loss_pct":  round(pos.profit_loss_percent or 0, 2),
    }
