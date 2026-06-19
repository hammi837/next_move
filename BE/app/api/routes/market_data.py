"""
Market-data route module.

Provides endpoints for retrieving real-time prices, historical OHLCV data,
trending symbols, and technical indicators.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import PaginationParams, get_db_session
from app.schemas.market_data import MarketDataResponse

router = APIRouter(
    prefix="/api/market-data",
    tags=["Market Data"],
)


@router.get(
    "/trending",
    response_model=list[dict],
    summary="Get trending symbols",
)
def get_trending_symbols(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Return a list of currently trending / most-active symbols."""
    # Placeholder – replace with real service call
    trending = [
        {"symbol": "AAPL", "name": "Apple Inc.", "change_pct": 2.34},
        {"symbol": "XAUUSD", "name": "Gold Spot", "change_pct": 1.12},
        {"symbol": "TSLA", "name": "Tesla Inc.", "change_pct": -0.87},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "change_pct": 0.56},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "change_pct": 1.78},
    ]
    return trending[:limit]


@router.get(
    "/{symbol}",
    response_model=dict,
    summary="Get current price for a symbol",
)
def get_current_price(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Fetch the latest price data for the given *symbol*."""
    from app.services.data_collector import DataCollectorService

    service = DataCollectorService()
    try:
        data = await service.collect_realtime(symbol)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch price for {symbol}: {exc}",
        )
    return data


@router.get(
    "/{symbol}/history",
    response_model=list[dict],
    summary="Get historical OHLCV data",
)
def get_history(
    symbol: str,
    start: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Candle interval (1d, 1h, 15m …)"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Return historical OHLCV bars for *symbol*."""
    from app.services.data_collector import DataCollectorService

    service = DataCollectorService()
    try:
        history = await service.collect_historical(
            symbol=symbol,
            start=start,
            end=end,
            interval=interval,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch history for {symbol}: {exc}",
        )
    # Apply simple pagination
    start_idx = pagination.offset
    end_idx = start_idx + pagination.page_size
    return history[start_idx:end_idx]


@router.get(
    "/{symbol}/indicators",
    response_model=dict,
    summary="Get technical indicators",
)
def get_indicators(
    symbol: str,
    indicators: str = Query(
        "rsi,macd,sma_20",
        description="Comma-separated list of indicator names",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Compute and return requested technical indicators for *symbol*."""
    from app.services.technical_analysis import TechnicalAnalysisService

    service = TechnicalAnalysisService()
    indicator_list = [i.strip() for i in indicators.split(",")]
    try:
        result = await service.calculate_all(symbol=symbol, indicators=indicator_list)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Indicator calculation failed: {exc}",
        )
    return result
