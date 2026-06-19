from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import PriceHistory, MarketMetadata
from app.services.market_data import market_data_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get complete dashboard summary with all markets."""
    try:
        cache_key = "dashboard_summary"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        # Fetch latest prices from MarketMetadata instead of blocking yfinance calls
        markets = db.query(MarketMetadata).filter(MarketMetadata.is_active == 1).all()

        gold = None
        stocks = []
        commodities = []

        for m in markets:
            data = {
                "symbol": m.symbol,
                "current_price": m.last_price,
                "change_percent_24h": 0, # We'll calculate this if needed
                "market_type": m.market_type.value if m.market_type else None,
                "timestamp": m.last_update.isoformat() if m.last_update else datetime.utcnow().isoformat()
            }
            if m.symbol == "GOLD":
                gold = data
            elif m.market_type and m.market_type.value == "stock":
                stocks.append(data)
            elif m.market_type and m.market_type.value == "commodity":
                commodities.append(data)

        # If DB is empty, try returning empty arrays instead of hanging
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

        cache_service.set(cache_key, response, ex=120)
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
