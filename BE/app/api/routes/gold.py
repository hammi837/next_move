from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List
import logging

from app.db.database import get_db
from app.db.models import PriceHistory, MarketMetadata, MarketType
from app.db.schemas import PriceHistoryResponse
from app.services.market_data import market_data_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/current", response_model=dict)
def get_current_gold_price(db: Session = Depends(get_db)):
    """Get current gold price."""
    try:
        cache_key = "gold_current_price"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        gold_data = market_data_service.fetch_gold_price_forex()
        if not gold_data:
            raise HTTPException(status_code=503, detail="Unable to fetch gold data")

        # Previous close for 24h change
        latest_db = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == "GOLD")
            .order_by(desc(PriceHistory.timestamp))
            .first()
        )

        response = {
            "symbol": "GOLD",
            "current_price": gold_data["price"],
            "open": gold_data["open"],
            "high": gold_data["high"],
            "low": gold_data["low"],
            "volume": gold_data["volume"],
            "timestamp": gold_data["timestamp"],
            "change_24h": None,
            "change_percent_24h": None,
        }

        if latest_db and latest_db.close_price:
            change = gold_data["price"] - latest_db.close_price
            pct = (change / latest_db.close_price) * 100
            response["change_24h"] = round(change, 2)
            response["change_percent_24h"] = round(pct, 2)

        cache_service.set(cache_key, response, ex=300)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current gold price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_gold_history(
    days: int = Query(7, ge=1, le=365),
    interval: str = Query("1d", pattern="^(1m|5m|15m|30m|1h|1d)$"),
    db: Session = Depends(get_db),
):
    """Get historical gold prices. interval: 1m,5m,15m,30m,1h for intraday; 1d for daily."""
    try:
        cache_key = f"gold_history_{days}d_{interval}"
        try:
            cached = cache_service.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass

        # For intraday intervals, always fetch live from yfinance (not stored in DB)
        if interval != "1d":
            period_map = {1: "1d", 2: "2d", 5: "5d", 7: "7d"}
            period = period_map.get(days, f"{days}d")
            historical = market_data_service.fetch_gold_historical(period=period, interval=interval)
            if not historical:
                return []
            result = [
                {
                    "symbol": "GOLD",
                    "open": r.get("Open"),
                    "high": r.get("High"),
                    "low": r.get("Low"),
                    "close": r.get("Close"),
                    "volume": r.get("Volume"),
                    "timestamp": r.get("Datetime", r.get("Date", "")).isoformat()
                        if hasattr(r.get("Datetime", r.get("Date", "")), "isoformat")
                        else str(r.get("Datetime", r.get("Date", ""))),
                }
                for r in historical
            ]
            try:
                cache_service.set(cache_key, result, ex=60)  # 1 min cache for intraday
            except Exception:
                pass
            return result

        start_date = datetime.utcnow() - timedelta(days=days)
        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == "GOLD", PriceHistory.timestamp >= start_date)
            .order_by(PriceHistory.timestamp)
            .all()
        )

        if not prices:
            # Fetch from API and store
            period_map = {7: "7d", 30: "1mo", 90: "3mo", 180: "6mo", 365: "1y"}
            period = period_map.get(days, f"{days}d")
            historical = market_data_service.fetch_gold_historical(period=period)
            if historical:
                for record in historical:
                    obj = PriceHistory(
                        symbol="GOLD",
                        market_type=MarketType.GOLD,
                        open_price=record.get("Open"),
                        high_price=record.get("High"),
                        low_price=record.get("Low"),
                        close_price=record.get("Close"),
                        volume=record.get("Volume"),
                        timestamp=record.get("Date"),
                    )
                    db.add(obj)
                db.commit()
                prices = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.symbol == "GOLD", PriceHistory.timestamp >= start_date)
                    .order_by(PriceHistory.timestamp)
                    .all()
                )

        result = [
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
            for p in prices
        ]
        try:
            cache_service.set(cache_key, result, ex=3600)
        except Exception:
            pass
        return result

    except Exception as e:
        logger.error(f"Error fetching gold history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_gold_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get gold market statistics."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == "GOLD", PriceHistory.timestamp >= start_date)
            .order_by(PriceHistory.timestamp)
            .all()
        )

        if not prices:
            return {"symbol": "GOLD", "period_days": days, "data_points": 0}

        closes = [p.close_price for p in prices if p.close_price]
        highs = [p.high_price for p in prices if p.high_price]
        lows = [p.low_price for p in prices if p.low_price]

        return {
            "symbol": "GOLD",
            "period_days": days,
            "data_points": len(prices),
            "current_price": closes[-1] if closes else None,
            "period_high": max(highs) if highs else None,
            "period_low": min(lows) if lows else None,
            "avg_price": round(sum(closes) / len(closes), 2) if closes else None,
            "price_change": round(closes[-1] - closes[0], 2) if len(closes) > 1 else None,
            "change_percent": round(((closes[-1] - closes[0]) / closes[0]) * 100, 2)
            if len(closes) > 1
            else None,
        }

    except Exception as e:
        logger.error(f"Error fetching gold stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
