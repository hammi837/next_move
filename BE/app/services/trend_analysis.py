"""
Historical trend analysis service.
Analyzes trend direction, momentum, reversals, and volatility.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from app.db.database import SessionLocal
from app.db.models import PriceHistory, MarketStats, TrendDirection
from sqlalchemy import desc

logger = logging.getLogger(__name__)


def _get_closes(symbol: str, days: int) -> Optional[np.ndarray]:
    db = SessionLocal()
    try:
        start = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol, PriceHistory.timestamp >= start)
            .order_by(PriceHistory.timestamp)
            .all()
        )
        if len(rows) < 5:
            return None
        return np.array([r.close_price for r in rows if r.close_price], dtype=float)
    finally:
        db.close()


class TrendAnalysisService:

    def analyze_symbol(self, symbol: str, days: int = 90) -> Dict:
        db = SessionLocal()
        try:
            start = datetime.utcnow() - timedelta(days=days)
            rows = (
                db.query(PriceHistory)
                .filter(PriceHistory.symbol == symbol, PriceHistory.timestamp >= start)
                .order_by(PriceHistory.timestamp)
                .all()
            )
            if len(rows) < 10:
                return {"error": "Insufficient data", "symbol": symbol}

            closes = np.array([r.close_price for r in rows if r.close_price], dtype=float)
            n = len(closes)

            # Trend direction via MA cross
            short_ma = float(np.mean(closes[-10:])) if n >= 10 else float(closes[-1])
            long_ma  = float(np.mean(closes[-min(50, n):])) if n >= 5 else float(closes[-1])

            if short_ma > long_ma:
                direction = "up"
            elif short_ma < long_ma:
                direction = "down"
            else:
                direction = "sideways"

            # Trend strength via linear regression slope
            x = np.arange(min(20, n))
            y = closes[-min(20, n):]
            coef = np.polyfit(x, y, 1)
            norm_slope = abs(coef[0]) / np.mean(y) * 100 if np.mean(y) else 0

            if norm_slope > 2.0:
                strength = "very_strong"
            elif norm_slope > 1.0:
                strength = "strong"
            elif norm_slope > 0.5:
                strength = "moderate"
            elif norm_slope > 0.1:
                strength = "weak"
            else:
                strength = "no_trend"

            # Momentum
            period = min(10, n - 1)
            momentum = float((closes[-1] - closes[-period - 1]) / closes[-period - 1] * 100) if period > 0 else 0.0

            # Volatility
            returns = np.diff(closes) / closes[:-1] * 100
            mid = len(returns) // 2
            early_vol  = float(np.std(returns[:mid]))  if mid > 0          else 0.0
            recent_vol = float(np.std(returns[mid:]))  if len(returns) > mid else 0.0
            vol_trend  = "increasing" if recent_vol > early_vol else "decreasing"

            # Reversals (local extrema in last 30 candles)
            window = 3
            recent = closes[-30:] if n >= 30 else closes
            reversals = []
            for i in range(window, len(recent) - window):
                segment = recent[max(0, i - window): i + window]
                if recent[i] == np.max(segment):
                    reversals.append({"type": "peak",   "price": round(float(recent[i]), 2), "potential": "bearish"})
                elif recent[i] == np.min(segment):
                    reversals.append({"type": "valley", "price": round(float(recent[i]), 2), "potential": "bullish"})

            # Price breaks (>2% single-candle moves)
            breaks = []
            for i in range(1, min(n, 30)):
                chg = abs((closes[-i] - closes[-i-1]) / closes[-i-1]) * 100
                if chg > 2.0:
                    breaks.append({
                        "price":          round(float(closes[-i]), 2),
                        "change_percent": round(float(chg), 2),
                        "direction":      "up" if closes[-i] > closes[-i-1] else "down",
                    })

            analysis = {
                "symbol":      symbol,
                "period_days": days,
                "data_points": n,
                "timestamp":   datetime.utcnow().isoformat(),
                "trend": {
                    "direction": direction,
                    "strength":  strength,
                    "short_ma":  round(short_ma, 2),
                    "long_ma":   round(long_ma, 2),
                },
                "momentum": {
                    "current":      round(momentum, 2),
                    "interpretation": "bullish" if momentum > 0 else "bearish",
                },
                "price_action": {
                    "current":   round(float(closes[-1]), 2),
                    "high":      round(float(np.max(closes)), 2),
                    "low":       round(float(np.min(closes)), 2),
                    "reversals": reversals[-5:],
                    "breaks":    breaks[:5],
                },
                "volatility": {
                    "recent":   round(recent_vol, 4),
                    "early":    round(early_vol, 4),
                    "trend":    vol_trend,
                },
                "stats": {
                    "mean":  round(float(np.mean(closes)), 2),
                    "std":   round(float(np.std(closes)), 2),
                    "range": round(float(np.max(closes) - np.min(closes)), 2),
                },
            }

            # Store summary in MarketStats
            try:
                stat = MarketStats(
                    symbol=symbol,
                    date=datetime.utcnow(),
                    open_price=float(closes[0]),
                    close_price=float(closes[-1]),
                    high_price=float(np.max(closes)),
                    low_price=float(np.min(closes)),
                    change_percent=round(momentum, 2),
                    trend=TrendDirection(direction) if direction in ("up", "down") else TrendDirection.NEUTRAL,
                )
                db.add(stat)
                db.commit()
            except Exception as e:
                logger.warning(f"Could not store trend stats for {symbol}: {e}")
                db.rollback()

            return analysis

        except Exception as e:
            logger.error(f"Trend analysis failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
        finally:
            db.close()


# Singleton
trend_analysis_service = TrendAnalysisService()
