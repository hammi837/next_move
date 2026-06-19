from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List
import logging

from app.db.database import get_db
from app.db.models import PriceHistory, MarketMetadata, MarketType
from app.services.market_data import market_data_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]


@router.get("/current/{symbol}")
def get_stock_price(symbol: str, db: Session = Depends(get_db)):
    """Get current stock price."""
    try:
        symbol = symbol.upper()
        cache_key = f"stock_api_{symbol}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        stock_data = market_data_service.fetch_stock_price(symbol)
        if not stock_data:
            raise HTTPException(status_code=503, detail=f"Unable to fetch data for {symbol}")

        latest_db = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol)
            .order_by(desc(PriceHistory.timestamp))
            .first()
        )

        response = {
            "symbol": symbol,
            "current_price": stock_data["price"],
            "open": stock_data["open"],
            "high": stock_data["high"],
            "low": stock_data["low"],
            "volume": stock_data["volume"],
            "timestamp": stock_data["timestamp"],
            "change_24h": None,
            "change_percent_24h": None,
        }

        if latest_db and latest_db.close_price:
            change = stock_data["price"] - latest_db.close_price
            pct = (change / latest_db.close_price) * 100
            response["change_24h"] = round(change, 2)
            response["change_percent_24h"] = round(pct, 2)

        cache_service.set(cache_key, response, ex=300)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
def get_stock_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get historical stock prices."""
    try:
        symbol = symbol.upper()
        start_date = datetime.utcnow() - timedelta(days=days)

        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol, PriceHistory.timestamp >= start_date)
            .order_by(PriceHistory.timestamp)
            .all()
        )

        if not prices:
            period_map = {7: "7d", 30: "1mo", 90: "3mo", 180: "6mo", 365: "1y"}
            period = period_map.get(days, f"{days}d")
            historical = market_data_service.fetch_stock_historical(symbol, period=period)
            if historical:
                for rec in historical:
                    db.add(
                        PriceHistory(
                            symbol=symbol,
                            market_type=MarketType.STOCK,
                            open_price=rec.get("Open"),
                            high_price=rec.get("High"),
                            low_price=rec.get("Low"),
                            close_price=rec.get("Close"),
                            volume=rec.get("Volume"),
                            timestamp=rec.get("Date"),
                        )
                    )
                db.commit()
                prices = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.symbol == symbol, PriceHistory.timestamp >= start_date)
                    .order_by(PriceHistory.timestamp)
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
            for p in prices
        ]

    except Exception as e:
        logger.error(f"Error fetching stock history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
def get_stocks_overview(db: Session = Depends(get_db)):
    """Get overview of tracked stocks."""
    try:
        cache_key = "stocks_overview"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        results = []
        for symbol in DEFAULT_STOCKS:
            data = market_data_service.fetch_stock_price(symbol)
            if data:
                results.append(data)

        cache_service.set(cache_key, results, ex=300)
        return results

    except Exception as e:
        logger.error(f"Error fetching stocks overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{symbol}")
def get_stock_stats(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get stock market statistics."""
    try:
        symbol = symbol.upper()
        start_date = datetime.utcnow() - timedelta(days=days)

        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol, PriceHistory.timestamp >= start_date)
            .order_by(PriceHistory.timestamp)
            .all()
        )

        if not prices:
            return {"symbol": symbol, "period_days": days, "data_points": 0}

        closes = [p.close_price for p in prices if p.close_price]
        highs = [p.high_price for p in prices if p.high_price]
        lows = [p.low_price for p in prices if p.low_price]

        return {
            "symbol": symbol,
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
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
