"""
Technical analysis service.
Computes RSI, MACD, Bollinger Bands, moving averages, ATR, ADX, Stochastic, OBV.
Uses pure numpy/pandas — no TA-Lib dependency required.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.db.database import SessionLocal
from app.db.models import PriceHistory, TechnicalIndicators
from app.services.cache_service import cache_service
from sqlalchemy import desc

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if np.isnan(f) or np.isinf(f) else round(f, 4)
    except Exception:
        return None


def _get_price_df(symbol: str, days: int = 120) -> Optional[pd.DataFrame]:
    """Fetch OHLCV from DB and return a clean DataFrame."""
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
        df = pd.DataFrame([{
            "timestamp": r.timestamp,
            "open":   r.open_price  or 0.0,
            "high":   r.high_price  or 0.0,
            "low":    r.low_price   or 0.0,
            "close":  r.close_price or 0.0,
            "volume": r.volume      or 0.0,
        } for r in rows])
        df = df.dropna(subset=["close"])
        df = df[df["close"] > 0]
        return df if len(df) >= 5 else None
    finally:
        db.close()


# ── Individual indicator functions ────────────────────────────────────────

def calc_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(closes: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger(closes: pd.Series, period=20, num_std=2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    middle = calc_sma(closes, period)
    std = closes.rolling(window=period, min_periods=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


def calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    up_move   = high.diff()
    down_move = -low.diff()
    plus_dm  = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr = calc_atr(high, low, close, period)
    plus_di  = 100 * calc_ema(plus_dm,  period) / atr.replace(0, np.nan)
    minus_di = 100 * calc_ema(minus_dm, period) / atr.replace(0, np.nan)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    return calc_ema(dx, period)


def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k=14, d=3) -> Tuple[pd.Series, pd.Series]:
    lowest_low   = low.rolling(window=k,  min_periods=k).min()
    highest_high = high.rolling(window=k, min_periods=k).max()
    k_line = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d_line = k_line.rolling(window=d, min_periods=d).mean()
    return k_line, d_line


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def calc_roc(closes: pd.Series, period=12) -> pd.Series:
    return closes.pct_change(periods=period) * 100


# ── Service class ────────────────────────────────────────────────────────

class TechnicalAnalysisService:
    """Calculates technical indicators from DB price history."""

    # ── Single-indicator helpers (kept async for route compatibility) ──

    async def calculate_rsi(self, closes: pd.Series, period: int = 14) -> pd.Series:
        return calc_rsi(closes, period)

    async def calculate_macd(self, closes: pd.Series, fast=12, slow=26, signal=9) -> Dict:
        ml, sl, hist = calc_macd(closes, fast, slow, signal)
        return {"macd": ml, "signal": sl, "histogram": hist}

    async def calculate_bollinger(self, closes: pd.Series, period=20, num_std=2.0) -> Dict:
        u, m, l = calc_bollinger(closes, period, num_std)
        return {"upper": u, "middle": m, "lower": l}

    async def calculate_moving_averages(self, closes: pd.Series, periods: List[int] = None) -> Dict:
        if periods is None:
            periods = [20, 50, 200]
        result = {}
        for p in periods:
            result[f"sma_{p}"] = calc_sma(closes, p)
            result[f"ema_{p}"] = calc_ema(closes, p)
        return result

    # ── Full analysis ────────────────────────────────────────────────────

    def calculate_all_indicators(self, symbol: str, days: int = 120) -> Optional[Dict]:
        """Calculate all indicators for a symbol. Returns dict or None."""
        cache_key = f"indicators_{symbol}_{days}d"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        df = _get_price_df(symbol, days)
        if df is None:
            logger.warning(f"Insufficient price data for {symbol}")
            return None

        closes = df["close"]
        highs  = df["high"]
        lows   = df["low"]
        volume = df["volume"]
        n = len(closes)

        # Moving averages
        sma_20  = _safe_float(calc_sma(closes, 20).iloc[-1])  if n >= 20  else None
        sma_50  = _safe_float(calc_sma(closes, 50).iloc[-1])  if n >= 50  else None
        sma_200 = _safe_float(calc_sma(closes, 200).iloc[-1]) if n >= 200 else None
        ema_12  = _safe_float(calc_ema(closes, 12).iloc[-1])
        ema_26  = _safe_float(calc_ema(closes, 26).iloc[-1])

        # RSI
        rsi_vals = calc_rsi(closes, 14)
        rsi_14 = _safe_float(rsi_vals.iloc[-1])

        # MACD
        ml, sl, hist = calc_macd(closes)
        macd_data = {
            "line":      _safe_float(ml.iloc[-1]),
            "signal":    _safe_float(sl.iloc[-1]),
            "histogram": _safe_float(hist.iloc[-1]),
        }

        # Bollinger Bands
        bb_u, bb_m, bb_l = calc_bollinger(closes)
        bb_data = {
            "upper":  _safe_float(bb_u.iloc[-1]),
            "middle": _safe_float(bb_m.iloc[-1]),
            "lower":  _safe_float(bb_l.iloc[-1]),
        }

        # ATR / ADX
        atr_14 = _safe_float(calc_atr(highs, lows, closes, 14).iloc[-1]) if n >= 14 else None
        adx_14 = _safe_float(calc_adx(highs, lows, closes, 14).iloc[-1]) if n >= 28 else None

        # Stochastic
        k, d = calc_stochastic(highs, lows, closes)
        stoch = {"k": _safe_float(k.iloc[-1]), "d": _safe_float(d.iloc[-1])}

        # OBV
        obv = _safe_float(calc_obv(closes, volume).iloc[-1])

        # ROC
        roc_12 = _safe_float(calc_roc(closes, 12).iloc[-1]) if n >= 12 else None

        # Price context
        current_price = _safe_float(closes.iloc[-1])

        result = {
            "symbol":       symbol,
            "timestamp":    datetime.utcnow().isoformat(),
            "data_points":  n,
            "current_price": current_price,
            "sma_20":  sma_20,
            "sma_50":  sma_50,
            "sma_200": sma_200,
            "ema_12":  ema_12,
            "ema_26":  ema_26,
            "rsi_14":  rsi_14,
            "macd":    macd_data,
            "bollinger_bands": bb_data,
            "atr_14":  atr_14,
            "adx_14":  adx_14,
            "stochastic": stoch,
            "obv":     obv,
            "roc_12":  roc_12,
            "signals": self._generate_signals(current_price, rsi_14, macd_data, bb_data, adx_14),
        }

        cache_service.set(cache_key, result, ex=3600)
        return result

    def _generate_signals(self, price, rsi, macd, bb, adx) -> Dict:
        """Generate buy/sell signals from indicator values."""
        buy_signals, sell_signals, neutral = [], [], []
        score = 0.0

        if rsi is not None:
            if rsi < 30:
                buy_signals.append("RSI_OVERSOLD")
                score += 0.35
            elif rsi > 70:
                sell_signals.append("RSI_OVERBOUGHT")
                score -= 0.35
            else:
                neutral.append("RSI_NEUTRAL")

        if macd.get("line") and macd.get("signal"):
            if macd["line"] > macd["signal"]:
                buy_signals.append("MACD_BULLISH_CROSS")
                score += 0.25
            else:
                sell_signals.append("MACD_BEARISH_CROSS")
                score -= 0.25

        if price and bb.get("upper") and bb.get("lower"):
            if price > bb["upper"]:
                sell_signals.append("BB_UPPER_BREACH")
                score -= 0.2
            elif price < bb["lower"]:
                buy_signals.append("BB_LOWER_BREACH")
                score += 0.2

        if adx is not None:
            if adx > 25:
                neutral.append("ADX_STRONG_TREND")
            else:
                neutral.append("ADX_WEAK_TREND")

        score = max(-1.0, min(1.0, score))
        if score > 0.2:
            overall = "BUY"
        elif score < -0.2:
            overall = "SELL"
        else:
            overall = "HOLD"

        return {
            "overall":       overall,
            "score":         round(score, 2),
            "buy_signals":   buy_signals,
            "sell_signals":  sell_signals,
            "neutral":       neutral,
        }

    def store_indicators(self, symbol: str, indicators: Dict) -> bool:
        """Persist calculated indicators to the database."""
        db = SessionLocal()
        try:
            latest = (
                db.query(PriceHistory)
                .filter(PriceHistory.symbol == symbol)
                .order_by(desc(PriceHistory.timestamp))
                .first()
            )
            if not latest:
                return False

            row = TechnicalIndicators(
                symbol=symbol,
                timestamp=latest.timestamp,
                sma_20=indicators.get("sma_20"),
                sma_50=indicators.get("sma_50"),
                ema_12=indicators.get("ema_12"),
                ema_26=indicators.get("ema_26"),
                rsi=indicators.get("rsi_14"),
                macd=indicators.get("macd", {}).get("line"),
                macd_signal=indicators.get("macd", {}).get("signal"),
                bollinger_upper=indicators.get("bollinger_bands", {}).get("upper"),
                bollinger_middle=indicators.get("bollinger_bands", {}).get("middle"),
                bollinger_lower=indicators.get("bollinger_bands", {}).get("lower"),
            )
            db.add(row)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing indicators for {symbol}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # ── async wrapper for route compatibility ────────────────────────────
    async def calculate_all(self, symbol: str) -> Dict:
        result = self.calculate_all_indicators(symbol)
        return result or {"symbol": symbol, "message": "Insufficient data"}


# Singleton
technical_analysis_service = TechnicalAnalysisService()
