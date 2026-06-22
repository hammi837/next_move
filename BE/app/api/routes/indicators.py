"""
Phase 2 – Technical Indicators & Analysis endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.services.technical_analysis import technical_analysis_service
from app.services.pattern_recognition import pattern_recognition_service
from app.services.trend_analysis import trend_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Full analysis ────────────────────────────────────────────────────────

@router.get("/{symbol}/indicators")
def get_indicators(
    symbol: str,
    days: int = Query(120, ge=20, le=365),
    db: Session = Depends(get_db),
):
    """All technical indicators for a symbol."""
    symbol = symbol.upper()
    result = technical_analysis_service.calculate_all_indicators(symbol, days)
    if not result:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
    return result


# ── Individual indicators ────────────────────────────────────────────────

@router.get("/{symbol}/rsi")
def get_rsi(
    symbol: str,
    period: int = Query(14, ge=5, le=50),
    db: Session = Depends(get_db),
):
    from app.services.technical_analysis import _get_price_df, calc_rsi, _safe_float
    symbol = symbol.upper()
    df = _get_price_df(symbol)
    if df is None:
        raise HTTPException(status_code=404, detail="Insufficient data")

    rsi_series = calc_rsi(df["close"], period)
    current = _safe_float(rsi_series.iloc[-1])

    if current is None:
        interpretation = "N/A"
    elif current < 30:
        interpretation = "OVERSOLD – potential BUY"
    elif current > 70:
        interpretation = "OVERBOUGHT – potential SELL"
    else:
        interpretation = "NEUTRAL"

    history = [_safe_float(v) for v in rsi_series.tail(30)]
    return {
        "symbol":         symbol,
        "period":         period,
        "current_rsi":    current,
        "interpretation": interpretation,
        "history":        history,
    }


@router.get("/{symbol}/macd")
def get_macd(symbol: str, db: Session = Depends(get_db)):
    from app.services.technical_analysis import _get_price_df, calc_macd, _safe_float
    symbol = symbol.upper()
    df = _get_price_df(symbol)
    if df is None:
        raise HTTPException(status_code=404, detail="Insufficient data")

    ml, sl, hist = calc_macd(df["close"])
    line   = _safe_float(ml.iloc[-1])
    signal = _safe_float(sl.iloc[-1])

    return {
        "symbol":        symbol,
        "macd_line":     line,
        "signal_line":   signal,
        "histogram":     _safe_float(hist.iloc[-1]),
        "signal":        "BULLISH" if (line and signal and line > signal) else "BEARISH",
        "history": {
            "macd":   [_safe_float(v) for v in ml.tail(30)],
            "signal": [_safe_float(v) for v in sl.tail(30)],
        }
    }


@router.get("/{symbol}/bollinger")
def get_bollinger(symbol: str, db: Session = Depends(get_db)):
    from app.services.technical_analysis import _get_price_df, calc_bollinger, _safe_float
    symbol = symbol.upper()
    df = _get_price_df(symbol)
    if df is None:
        raise HTTPException(status_code=404, detail="Insufficient data")

    u, m, l = calc_bollinger(df["close"])
    price   = float(df["close"].iloc[-1])
    upper   = _safe_float(u.iloc[-1])
    lower   = _safe_float(l.iloc[-1])
    position = round((price - lower) / (upper - lower) * 100, 1) if upper and lower and upper != lower else None

    return {
        "symbol":           symbol,
        "current_price":    round(price, 2),
        "upper_band":       upper,
        "middle_band":      _safe_float(m.iloc[-1]),
        "lower_band":       lower,
        "position_in_band": position,
    }


@router.get("/{symbol}/stochastic")
def get_stochastic(symbol: str, db: Session = Depends(get_db)):
    from app.services.technical_analysis import _get_price_df, calc_stochastic, _safe_float
    symbol = symbol.upper()
    df = _get_price_df(symbol)
    if df is None:
        raise HTTPException(status_code=404, detail="Insufficient data")

    k, d = calc_stochastic(df["high"], df["low"], df["close"])
    kv = _safe_float(k.iloc[-1])
    dv = _safe_float(d.iloc[-1])

    if kv and kv < 20:
        signal = "OVERSOLD"
    elif kv and kv > 80:
        signal = "OVERBOUGHT"
    else:
        signal = "NEUTRAL"

    return {"symbol": symbol, "k": kv, "d": dv, "signal": signal}


# ── Pattern recognition ───────────────────────────────────────────────────

@router.get("/{symbol}/patterns/candlestick")
async def get_candlestick_patterns(
    symbol: str,
    lookback: int = Query(20, ge=5, le=60),
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()
    patterns = await pattern_recognition_service.detect_candlestick_patterns(symbol, lookback)
    bullish = sum(1 for p in patterns if p["signal"] == "bullish")
    bearish = sum(1 for p in patterns if p["signal"] == "bearish")
    return {
        "symbol":            symbol,
        "detected_patterns": patterns,
        "bullish_count":     bullish,
        "bearish_count":     bearish,
        "bias":              "bullish" if bullish > bearish else ("bearish" if bearish > bullish else "neutral"),
    }


@router.get("/{symbol}/patterns/trend")
def get_trend_patterns(
    symbol: str,
    lookback: int = Query(50, ge=10, le=200),
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()
    patterns = pattern_recognition_service.detect_trend_patterns(symbol, lookback)
    if not patterns:
        raise HTTPException(status_code=404, detail="Insufficient data")
    return {"symbol": symbol, **patterns}


@router.get("/{symbol}/support-resistance")
async def get_support_resistance(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    levels = await pattern_recognition_service.find_support_resistance(symbol)
    return {"symbol": symbol, **levels}


# ── Trend analysis ────────────────────────────────────────────────────────

@router.get("/{symbol}/trend-analysis")
def get_trend_analysis(
    symbol: str,
    days: int = Query(90, ge=20, le=365),
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()
    result = trend_analysis_service.analyze_symbol(symbol, days)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{symbol}/trend")
async def get_trend(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    trend = await pattern_recognition_service.detect_trend(symbol)
    return {"symbol": symbol, **trend}


# ── Summary (all-in-one for the frontend) ────────────────────────────────

@router.get("/{symbol}/summary")
async def get_analysis_summary(
    symbol: str,
    days: int = Query(90, ge=20, le=365),
    db: Session = Depends(get_db),
):
    """Single endpoint that returns indicators + patterns + trend for the UI."""
    symbol = symbol.upper()

    indicators  = technical_analysis_service.calculate_all_indicators(symbol, days)
    trend       = await pattern_recognition_service.detect_trend(symbol)
    patterns    = await pattern_recognition_service.detect_candlestick_patterns(symbol, 20)
    sr_levels   = await pattern_recognition_service.find_support_resistance(symbol)
    trend_analysis = trend_analysis_service.analyze_symbol(symbol, days)

    return {
        "symbol":         symbol,
        "indicators":     indicators,
        "trend":          trend,
        "patterns":       patterns[-5:],  # last 5 patterns
        "support_resistance": sr_levels,
        "trend_analysis": trend_analysis,
    }
