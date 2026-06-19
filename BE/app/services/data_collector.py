"""
Data collector service.

Orchestrates fetching market data from multiple external sources
and persisting it to the database.
"""

from datetime import date, datetime
from typing import Any, Optional

import pandas as pd


class DataCollectorService:
    """Collects and normalises market data from external APIs."""

    def __init__(self) -> None:
        from app.data_sources.yahoo_finance import YahooFinanceConnector
        from app.data_sources.alpha_vantage import AlphaVantageConnector

        self.yahoo = YahooFinanceConnector()
        self.alpha_vantage = AlphaVantageConnector()

    async def collect_historical(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        """
        Fetch historical OHLCV data for *symbol*.

        Falls back to Alpha Vantage if Yahoo Finance fails.
        """
        try:
            df = await self.yahoo.get_history(
                symbol=symbol, start=start, end=end, interval=interval
            )
        except Exception:
            df = await self.alpha_vantage.get_daily(symbol=symbol)

        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return []

        if isinstance(df, pd.DataFrame):
            records = df.reset_index().to_dict(orient="records")
        else:
            records = df

        return [
            {
                "symbol": symbol.upper(),
                "timestamp": str(r.get("Date", r.get("timestamp", ""))),
                "open": float(r.get("Open", r.get("open", 0))),
                "high": float(r.get("High", r.get("high", 0))),
                "low": float(r.get("Low", r.get("low", 0))),
                "close": float(r.get("Close", r.get("close", 0))),
                "volume": float(r.get("Volume", r.get("volume", 0))),
            }
            for r in records
        ]

    async def collect_realtime(self, symbol: str) -> dict[str, Any]:
        """Fetch the latest real-time price for *symbol*."""
        try:
            info = await self.yahoo.get_price(symbol)
        except Exception:
            info = {
                "symbol": symbol.upper(),
                "price": 0.0,
                "change": 0.0,
                "change_pct": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }
        return info

    async def collect_indicators(
        self,
        symbol: str,
        indicators: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch pre-computed indicators from Alpha Vantage."""
        try:
            data = await self.alpha_vantage.get_indicators(
                symbol=symbol, indicators=indicators or ["SMA", "RSI"]
            )
        except Exception:
            data = {"symbol": symbol.upper(), "indicators": {}}
        return data
