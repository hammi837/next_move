"""
Pattern recognition service.
Detects candlestick patterns, support/resistance levels, and trend direction.
Uses pure pandas/numpy.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.db.database import SessionLocal
from app.db.models import PriceHistory
from sqlalchemy import desc

logger = logging.getLogger(__name__)


def _get_ohlcv(symbol: str, limit: int = 60) -> Optional[pd.DataFrame]:
    db = SessionLocal()
    try:
        rows = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol)
            .order_by(desc(PriceHistory.timestamp))
            .limit(limit)
            .all()
        )
        if not rows:
            return None
        rows = list(reversed(rows))
        return pd.DataFrame([{
            "timestamp": r.timestamp,
            "open":   r.open_price  or 0.0,
            "high":   r.high_price  or 0.0,
            "low":    r.low_price   or 0.0,
            "close":  r.close_price or 0.0,
            "volume": r.volume      or 0.0,
        } for r in rows])
    finally:
        db.close()


class PatternRecognitionService:
    """Identify candlestick patterns, support/resistance, and trend from DB data."""

    # ── Candlestick detectors ─────────────────────────────────────────────

    @staticmethod
    def _is_doji(o, h, l, c) -> bool:
        rng = h - l
        return rng > 0 and abs(c - o) / rng < 0.1

    @staticmethod
    def _is_hammer(o, h, l, c) -> bool:
        body = abs(c - o)
        rng  = h - l
        if rng == 0:
            return False
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        return lower_wick > 2 * body and upper_wick < body and body < 0.3 * rng

    @staticmethod
    def _is_inverted_hammer(o, h, l, c) -> bool:
        body = abs(c - o)
        rng  = h - l
        if rng == 0:
            return False
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        return upper_wick > 2 * body and lower_wick < body and body < 0.3 * rng

    @staticmethod
    def _is_bullish_engulfing(p, c) -> bool:
        return (p["close"] < p["open"] and c["close"] > c["open"]
                and c["open"] < p["close"] and c["close"] > p["open"])

    @staticmethod
    def _is_bearish_engulfing(p, c) -> bool:
        return (p["close"] > p["open"] and c["close"] < c["open"]
                and c["open"] > p["close"] and c["close"] < p["open"])

    @staticmethod
    def _is_morning_star(c1, c2, c3) -> bool:
        body1 = abs(c1["close"] - c1["open"])
        body2 = abs(c2["close"] - c2["open"])
        body3 = abs(c3["close"] - c3["open"])
        return (c1["close"] < c1["open"] and body2 < body1 * 0.5
                and c3["close"] > c3["open"] and body3 > body1 * 0.5)

    @staticmethod
    def _is_evening_star(c1, c2, c3) -> bool:
        body1 = abs(c1["close"] - c1["open"])
        body2 = abs(c2["close"] - c2["open"])
        body3 = abs(c3["close"] - c3["open"])
        return (c1["close"] > c1["open"] and body2 < body1 * 0.5
                and c3["close"] < c3["open"] and body3 > body1 * 0.5)

    # ── Public methods ────────────────────────────────────────────────────

    async def detect_candlestick_patterns(self, symbol: str, lookback: int = 20) -> List[Dict]:
        df = _get_ohlcv(symbol, max(lookback, 10))
        if df is None or len(df) < 3:
            return []

        patterns = []

        for i, row in df.iterrows():
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]
            ts = str(row["timestamp"])

            if self._is_doji(o, h, l, c):
                patterns.append({"pattern": "doji", "date": ts, "signal": "neutral", "confidence": 0.7})
            if self._is_hammer(o, h, l, c):
                patterns.append({"pattern": "hammer", "date": ts, "signal": "bullish", "confidence": 0.75})
            if self._is_inverted_hammer(o, h, l, c):
                patterns.append({"pattern": "inverted_hammer", "date": ts, "signal": "bullish", "confidence": 0.65})

            if i >= 1:
                p = df.iloc[i - 1]
                if self._is_bullish_engulfing(p, row):
                    patterns.append({"pattern": "bullish_engulfing", "date": ts, "signal": "bullish", "confidence": 0.80})
                if self._is_bearish_engulfing(p, row):
                    patterns.append({"pattern": "bearish_engulfing", "date": ts, "signal": "bearish", "confidence": 0.80})

            if i >= 2:
                c1 = df.iloc[i - 2]
                c2 = df.iloc[i - 1]
                c3 = row
                if self._is_morning_star(c1, c2, c3):
                    patterns.append({"pattern": "morning_star", "date": ts, "signal": "bullish", "confidence": 0.85})
                if self._is_evening_star(c1, c2, c3):
                    patterns.append({"pattern": "evening_star", "date": ts, "signal": "bearish", "confidence": 0.85})

        return patterns[-20:]

    async def find_support_resistance(self, symbol: str, window: int = 5, num_levels: int = 5) -> Dict:
        df = _get_ohlcv(symbol, 60)
        if df is None or len(df) < window * 2:
            return {"support": [], "resistance": []}

        highs = df["high"].values
        lows  = df["low"].values

        support_levels    = []
        resistance_levels = []

        for i in range(window, len(df) - window):
            if lows[i]  == min(lows[max(0, i-window):i+window]):
                support_levels.append(round(float(lows[i]), 2))
            if highs[i] == max(highs[max(0, i-window):i+window]):
                resistance_levels.append(round(float(highs[i]), 2))

        # Deduplicate close levels (within 0.5%)
        def cluster(levels, tol=0.005):
            levels = sorted(set(levels))
            result = []
            for lvl in levels:
                if not result or abs(lvl - result[-1]) / result[-1] > tol:
                    result.append(lvl)
            return result

        return {
            "support":    cluster(support_levels)[:num_levels],
            "resistance": list(reversed(cluster(resistance_levels)))[:num_levels],
        }

    async def detect_trend(self, symbol: str, short_window: int = 10, long_window: int = 30) -> Dict:
        df = _get_ohlcv(symbol, max(long_window + 10, 60))
        if df is None or len(df) < long_window:
            return {"direction": "unknown", "strength": 0.0}

        closes = df["close"]
        sma_short = closes.rolling(window=short_window).mean().iloc[-1]
        sma_long  = closes.rolling(window=long_window).mean().iloc[-1]
        current   = float(closes.iloc[-1])

        if sma_short > sma_long:
            direction = "bullish"
            strength  = min((sma_short - sma_long) / sma_long * 100, 100)
        elif sma_short < sma_long:
            direction = "bearish"
            strength  = min((sma_long - sma_short) / sma_long * 100, 100)
        else:
            direction = "neutral"
            strength  = 0.0

        return {
            "direction": direction,
            "strength":  round(float(strength), 2),
            "sma_short": round(float(sma_short), 2),
            "sma_long":  round(float(sma_long), 2),
            "current_price": round(current, 2),
        }

    def detect_trend_patterns(self, symbol: str, lookback: int = 50) -> Dict:
        """Synchronous version used by the indicators route."""
        df = _get_ohlcv(symbol, lookback)
        if df is None or len(df) < 10:
            return {}

        closes = df["close"].values
        x = np.arange(len(closes))
        coef = np.polyfit(x, closes, 1)
        slope = float(coef[0])
        mean  = float(np.mean(closes))
        norm_slope = slope / mean * 100 if mean else 0

        if norm_slope > 0.3:
            trend = "UPTREND"
        elif norm_slope < -0.3:
            trend = "DOWNTREND"
        else:
            trend = "SIDEWAYS"

        return {
            "trend": trend,
            "slope": round(slope, 4),
            "channel": {
                "upper": round(float(np.max(closes[-20:])), 2),
                "middle": round(float(np.mean(closes[-20:])), 2),
                "lower": round(float(np.min(closes[-20:])), 2),
            }
        }


# Singleton
pattern_recognition_service = PatternRecognitionService()
