"""
Technical analysis service.

Computes RSI, MACD, Bollinger Bands, moving averages, and more.
"""

from typing import Any

import numpy as np
import pandas as pd


class TechnicalAnalysisService:
    """Calculates common technical indicators from OHLCV data."""

    def __init__(self) -> None:
        pass

    async def calculate_rsi(
        self,
        closes: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Parameters
        ----------
        closes : pd.Series
            Series of closing prices.
        period : int
            Look-back period (default 14).

        Returns
        -------
        pd.Series
            RSI values.
        """
        delta = closes.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    async def calculate_macd(
        self,
        closes: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> dict[str, pd.Series]:
        """
        Calculate MACD, signal line, and histogram.

        Returns
        -------
        dict with keys: macd, signal, histogram
        """
        ema_fast = closes.ewm(span=fast, adjust=False).mean()
        ema_slow = closes.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }

    async def calculate_bollinger(
        self,
        closes: pd.Series,
        period: int = 20,
        num_std: float = 2.0,
    ) -> dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.

        Returns
        -------
        dict with keys: upper, middle, lower
        """
        middle = closes.rolling(window=period).mean()
        std = closes.rolling(window=period).std()
        upper = middle + num_std * std
        lower = middle - num_std * std
        return {"upper": upper, "middle": middle, "lower": lower}

    async def calculate_moving_averages(
        self,
        closes: pd.Series,
        periods: list[int] | None = None,
    ) -> dict[str, pd.Series]:
        """
        Calculate simple and exponential moving averages.

        Parameters
        ----------
        periods : list[int]
            List of MA periods (default [20, 50, 200]).
        """
        if periods is None:
            periods = [20, 50, 200]
        result: dict[str, pd.Series] = {}
        for p in periods:
            result[f"sma_{p}"] = closes.rolling(window=p).mean()
            result[f"ema_{p}"] = closes.ewm(span=p, adjust=False).mean()
        return result

    async def calculate_all(
        self,
        symbol: str,
        indicators: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compute all requested indicators for *symbol*.

        This is a convenience wrapper that fetches data and runs
        every indicator calculation.
        """
        from app.services.data_collector import DataCollectorService

        collector = DataCollectorService()
        history = await collector.collect_historical(symbol=symbol)

        if not history:
            return {"symbol": symbol.upper(), "indicators": {}, "message": "No data"}

        df = pd.DataFrame(history)
        closes = pd.to_numeric(df["close"], errors="coerce")

        result: dict[str, Any] = {"symbol": symbol.upper()}

        # RSI
        rsi = await self.calculate_rsi(closes)
        result["rsi"] = float(rsi.iloc[-1]) if not rsi.empty else None

        # MACD
        macd = await self.calculate_macd(closes)
        result["macd"] = {
            "macd": float(macd["macd"].iloc[-1]),
            "signal": float(macd["signal"].iloc[-1]),
            "histogram": float(macd["histogram"].iloc[-1]),
        }

        # Bollinger
        bb = await self.calculate_bollinger(closes)
        result["bollinger"] = {
            "upper": float(bb["upper"].iloc[-1]),
            "middle": float(bb["middle"].iloc[-1]),
            "lower": float(bb["lower"].iloc[-1]),
        }

        # Moving averages
        mas = await self.calculate_moving_averages(closes)
        result["moving_averages"] = {
            k: float(v.iloc[-1]) for k, v in mas.items() if not v.empty
        }

        return result
