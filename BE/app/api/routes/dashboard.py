from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Dict
import logging

from app.db.database import get_db
from app.db.models import PriceHistory, MarketMetadata
from app.services.market_data import market_data_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _calc_change(db: Session, symbol: str, current_price: float):
    """Return (change_24h, change_percent_24h) using today vs previous trading day close."""
    try:
        from datetime import date, timedelta
        today = datetime.utcnow().date()

        # Get the two most recent DISTINCT trading days
        rows = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol)
            .order_by(desc(PriceHistory.timestamp))
            .limit(50)  # enough to find two distinct days
            .all()
        )

        days_seen = {}
        for row in rows:
            if row.timestamp and row.close_price:
                d = row.timestamp.date()
                if d not in days_seen:
                    days_seen[d] = row.close_price
                if len(days_seen) == 2:
                    break

        if len(days_seen) >= 2:
            sorted_days = sorted(days_seen.keys(), reverse=True)
            prev_close = days_seen[sorted_days[1]]  # older day's close
            change = round(current_price - prev_close, 2)
            pct = round((change / prev_close) * 100, 2)
            return change, pct

        # Only one day in DB — compare vs open of that day
        if rows and rows[-1].open_price:
            prev = rows[-1].open_price
            change = round(current_price - prev, 2)
            pct = round((change / prev) * 100, 2)
            return change, pct

    except Exception as e:
        logger.warning(f"Could not compute change for {symbol}: {e}")
    return None, None


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get complete dashboard summary with all markets."""
    try:
        cache_key = "dashboard_summary"
        try:
            cached = cache_service.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass

        markets = db.query(MarketMetadata).filter(MarketMetadata.is_active == 1).all()

        gold = None
        stocks = []
        commodities = []

        for m in markets:
            price = m.last_price or 0
            change_24h, change_pct = _calc_change(db, m.symbol, price)

            data = {
                "symbol": m.symbol,
                "current_price": price,
                "change_24h": change_24h,
                "change_percent_24h": change_pct,
                "market_type": m.market_type.value if m.market_type else None,
                "timestamp": m.last_update.isoformat() if m.last_update else datetime.utcnow().isoformat(),
            }
            if m.symbol == "GOLD":
                gold = data
            elif m.market_type and m.market_type.value == "stock":
                stocks.append(data)
            elif m.market_type and m.market_type.value == "commodity":
                commodities.append(data)

        if not markets:
            logger.warning("No market data found in DB. Is the background collector running?")

        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "gold": gold,
            "stocks": stocks,
            "commodities": commodities,
            "tracked_symbols": len(markets),
            "markets": {
                "gold": {"status": "active" if gold else "unavailable"},
                "stocks": {"status": "active", "count": len(stocks)},
                "commodities": {"status": "active", "count": len(commodities)},
            },
        }

        try:
            cache_service.set(cache_key, response, ex=120)
        except Exception:
            pass  # cache failure must never break the response
        return response

    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-overview")
def get_market_overview(db: Session = Depends(get_db)):
    """Get a quick overview of all tracked markets."""
    try:
        markets = db.query(MarketMetadata).filter(MarketMetadata.is_active == 1).all()

        return [
            {
                "symbol": m.symbol,
                "name": m.name,
                "market_type": m.market_type.value if m.market_type else None,
                "last_price": m.last_price,
                "last_update": m.last_update.isoformat() if m.last_update else None,
            }
            for m in markets
        ]
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-data/{symbol}")
def get_recent_data(symbol: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get the most recent price data for a symbol."""
    try:
        symbol = symbol.upper()
        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol)
            .order_by(desc(PriceHistory.timestamp))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": p.id,
                "symbol": p.symbol,
                "open": p.open_price,
                "high": p.high_price,
                "low": p.low_price,
                "close": p.close_price,
                "volume": p.volume,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            }
            for p in reversed(prices)
        ]
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
