"""
Analysis route module — fixed async/sync issues.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.technical_analysis import technical_analysis_service
from app.services.pattern_recognition import pattern_recognition_service

router = APIRouter()


@router.get("/{symbol}/technical")
def technical_analysis(
    symbol: str,
    days: int = Query(120, ge=20, le=365),
    db: Session = Depends(get_db),
):
    """Full technical analysis for a symbol."""
    symbol = symbol.upper()
    result = technical_analysis_service.calculate_all_indicators(symbol, days)
    if not result:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
    return {"symbol": symbol, "indicators": result}


@router.get("/{symbol}/patterns")
async def detect_patterns(symbol: str, db: Session = Depends(get_db)):
    """Detect candlestick and chart patterns."""
    symbol = symbol.upper()
    patterns = await pattern_recognition_service.detect_candlestick_patterns(symbol)
    trend    = await pattern_recognition_service.detect_trend(symbol)
    return {"symbol": symbol, "patterns": patterns, "trend": trend}


@router.get("/{symbol}/support-resistance")
async def support_resistance(symbol: str, db: Session = Depends(get_db)):
    """Key support and resistance levels."""
    symbol = symbol.upper()
    levels = await pattern_recognition_service.find_support_resistance(symbol)
    return {"symbol": symbol, "support_levels": levels["support"], "resistance_levels": levels["resistance"]}
