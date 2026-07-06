"""
Portfolio management service.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.db.models import Portfolio, Position

logger = logging.getLogger(__name__)


class PortfolioService:

    # ── Portfolio CRUD ────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, user_id: int, name: str,
               initial_investment: float = 0.0,
               description: str = "",
               risk_level: str = "medium") -> Portfolio:
        p = Portfolio(
            user_id            = user_id,
            name               = name,
            description        = description,
            initial_investment = initial_investment,
            current_value      = initial_investment,
            risk_level         = risk_level,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @staticmethod
    def list_for_user(db: Session, user_id: int) -> List[Portfolio]:
        return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    @staticmethod
    def get(db: Session, portfolio_id: int,
            user_id: int) -> Optional[Portfolio]:
        return db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id,
        ).first()

    @staticmethod
    def delete(db: Session, portfolio_id: int, user_id: int) -> bool:
        p = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id, Portfolio.user_id == user_id
        ).first()
        if not p:
            return False
        db.delete(p)
        db.commit()
        return True

    # ── Position CRUD ─────────────────────────────────────────────────────

    @staticmethod
    def add_position(db: Session, portfolio_id: int, symbol: str,
                     quantity: float, entry_price: float,
                     stop_loss: float = None,
                     take_profit: float = None) -> Position:
        pos = Position(
            portfolio_id  = portfolio_id,
            symbol        = symbol.upper(),
            quantity      = quantity,
            entry_price   = entry_price,
            current_price = entry_price,
            current_value = quantity * entry_price,
            profit_loss   = 0.0,
            profit_loss_percent = 0.0,
            stop_loss     = stop_loss,
            take_profit   = take_profit,
        )
        db.add(pos)
        db.commit()
        db.refresh(pos)
        return pos

    @staticmethod
    def close_position(db: Session, position_id: int,
                       exit_price: float) -> Optional[Position]:
        pos = db.query(Position).filter(Position.id == position_id).first()
        if not pos or pos.status != "open":
            return None
        pos.status      = "closed"
        pos.closed_date = datetime.utcnow()
        pos.current_price       = exit_price
        pos.current_value       = pos.quantity * exit_price
        pos.profit_loss         = pos.current_value - pos.quantity * pos.entry_price
        pos.profit_loss_percent = pos.profit_loss / (pos.quantity * pos.entry_price) * 100
        db.commit()
        db.refresh(pos)
        return pos

    @staticmethod
    def update_prices(db: Session, portfolio_id: int,
                      prices: Dict[str, float]) -> None:
        """Refresh current_price / current_value / pnl for open positions."""
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.status       == "open",
        ).all()
        for pos in positions:
            if pos.symbol in prices:
                cp = prices[pos.symbol]
                pos.current_price       = cp
                pos.current_value       = pos.quantity * cp
                pos.profit_loss         = pos.current_value - pos.quantity * pos.entry_price
                pos.profit_loss_percent = (pos.profit_loss /
                                           (pos.quantity * pos.entry_price) * 100)
        db.commit()

    # ── Metrics ───────────────────────────────────────────────────────────

    @staticmethod
    def metrics(db: Session, portfolio_id: int) -> Dict:
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.status       == "open",
        ).all()

        total_cost  = sum(p.quantity * p.entry_price for p in positions)
        total_value = sum((p.current_value or p.quantity * p.entry_price)
                          for p in positions)
        total_pnl   = total_value - total_cost
        pnl_pct     = (total_pnl / total_cost * 100) if total_cost else 0.0
        winners     = [p for p in positions if (p.profit_loss or 0) > 0]
        losers      = [p for p in positions if (p.profit_loss or 0) < 0]

        return {
            "portfolio_id":      portfolio_id,
            "open_positions":    len(positions),
            "total_invested":    round(total_cost,  2),
            "total_value":       round(total_value, 2),
            "total_pnl":         round(total_pnl,   2),
            "total_pnl_percent": round(pnl_pct,     2),
            "winning_positions": len(winners),
            "losing_positions":  len(losers),
            "win_rate":          round(len(winners) / len(positions) * 100, 1)
                                  if positions else 0.0,
            "positions": [
                {
                    "id":           p.id,
                    "symbol":       p.symbol,
                    "quantity":     p.quantity,
                    "entry_price":  p.entry_price,
                    "current_price": p.current_price,
                    "current_value": round(p.current_value or 0, 2),
                    "pnl":           round(p.profit_loss or 0, 2),
                    "pnl_pct":       round(p.profit_loss_percent or 0, 2),
                    "stop_loss":    p.stop_loss,
                    "take_profit":  p.take_profit,
                }
                for p in positions
            ],
        }


portfolio_service = PortfolioService()
