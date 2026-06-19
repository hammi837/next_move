"""
Pattern recognition service.

Detects support/resistance levels, candlestick patterns, and trends.
"""

from typing import Any

import numpy as np
import pandas as pd


class PatternRecognitionService:
    """Identifies chart and candlestick patterns from OHLCV data."""

    def __init__(self) -> None:
        pass

    async def find_support_resistance(
        self,
        symbol: str,
        window: int = 20,
        num_levels: int = 5,
    ) -> dict[str, list[float]]:
        """
        Identify key support and resistance price levels.

        Uses rolling-window local minima/maxima detection.
        """
        from app.services.data_collector import DataCollectorService

        collector = DataCollectorService()
        history = await collector.collect_historical(symbol=symbol)

        if not history:
            return {"support": [], "resistance": []}

        df = pd.DataFrame(history)
        highs = pd.to_numeric(df["high"], errors="coerce")
        lows = pd.to_numeric(df["low"], errors="coerce")

        # Local maxima → resistance
        rolling_max = highs.rolling(window=window, center=True).max()
        resistance_mask = highs == rolling_max
        resistance_levels = sorted(highs[resistance_mask].unique().tolist(), reverse=True)[
            :num_levels
        ]

        # Local minima → support
        rolling_min = lows.rolling(window=window, center=True).min()
        support_mask = lows == rolling_min
        support_levels = sorted(lows[support_mask].unique().tolist())[:num_levels]

        return {
            "support": [round(float(s), 2) for s in support_levels],
            "resistance": [round(float(r), 2) for r in resistance_levels],
        }

    async def detect_candlestick_patterns(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:
        """
        Detect common candlestick patterns in recent data.

        Returns a list of dicts with pattern name, date, and signal.
        """
        from app.services.data_collector import DataCollectorService

        collector = DataCollectorService()
        history = await collector.collect_historical(symbol=symbol)

        if len(history) < 3:
            return []

        patterns: list[dict[str, Any]] = []
        df = pd.DataFrame(history)

        for col in ("open", "high", "low", "close"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Simple doji detection (open ≈ close)
        for i in range(len(df)):
            row = df.iloc[i]
            body = abs(row["close"] - row["open"])
            full_range = row["high"] - row["low"]
            if full_range > 0 and body / full_range < 0.1:
                patterns.append(
                    {
                        "pattern": "doji",
                        "date": str(row.get("timestamp", "")),
                        "signal": "neutral",
                        "confidence": 0.7,
                    }
                )

        # Engulfing detection
        for i in range(1, len(df)):
            prev, curr = df.iloc[i - 1], df.iloc[i]
            if (
                prev["close"] < prev["open"]
                and curr["close"] > curr["open"]
                and curr["close"] > prev["open"]
                and curr["open"] < prev["close"]
            ):
                patterns.append(
                    {
                        "pattern": "bullish_engulfing",
                        "date": str(curr.get("timestamp", "")),
                        "signal": "bullish",
                        "confidence": 0.75,
                    }
                )
            elif (
                prev["close"] > prev["open"]
                and curr["close"] < curr["open"]
                and curr["close"] < prev["open"]
                and curr["open"] > prev["close"]
            ):
                patterns.append(
                    {
                        "pattern": "bearish_engulfing",
                        "date": str(curr.get("timestamp", "")),
                        "signal": "bearish",
                        "confidence": 0.75,
                    }
                )

        return patterns[-20:]  # Return most recent 20 patterns

    async def detect_trend(
        self,
        symbol: str,
        short_window: int = 20,
        long_window: int = 50,
    ) -> dict[str, Any]:
        """
        Detect the current trend using moving-average crossover.

        Returns the current trend direction and strength.
        """
        from app.services.data_collector import DataCollectorService

        collector = DataCollectorService()
        history = await collector.collect_historical(symbol=symbol)

        if len(history) < long_window:
            return {"direction": "unknown", "strength": 0.0}

        df = pd.DataFrame(history)
        closes = pd.to_numeric(df["close"], errors="coerce")

        sma_short = closes.rolling(window=short_window).mean()
        sma_long = closes.rolling(window=long_window).mean()

        latest_short = float(sma_short.iloc[-1])
        latest_long = float(sma_long.iloc[-1])

        if latest_short > latest_long:
            direction = "bullish"
            strength = min((latest_short - latest_long) / latest_long * 100, 100)
        elif latest_short < latest_long:
            direction = "bearish"
            strength = min((latest_long - latest_short) / latest_long * 100, 100)
        else:
            direction = "neutral"
            strength = 0.0

        return {
            "direction": direction,
            "strength": round(strength, 2),
            "sma_short": round(latest_short, 2),
            "sma_long": round(latest_long, 2),
        }
