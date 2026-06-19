"""
Analysis route module.

Provides endpoints for technical analysis, pattern recognition,
and support/resistance level detection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session

router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
)


@router.get(
    "/{symbol}/technical",
    response_model=dict,
    summary="Full technical analysis",
)
def technical_analysis(
    symbol: str,
    interval: str = Query("1d", description="Candle interval"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Run a comprehensive technical analysis on *symbol*."""
    from app.services.technical_analysis import TechnicalAnalysisService

    service = TechnicalAnalysisService()
    try:
        result = await service.calculate_all(symbol=symbol)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technical analysis failed: {exc}",
        )
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "indicators": result,
    }


@router.get(
    "/{symbol}/patterns",
    response_model=dict,
    summary="Detect chart patterns",
)
def detect_patterns(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Detect candlestick and chart patterns for *symbol*."""
    from app.services.pattern_recognition import PatternRecognitionService

    service = PatternRecognitionService()
    try:
        patterns = await service.detect_candlestick_patterns(symbol=symbol)
        trend = await service.detect_trend(symbol=symbol)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern detection failed: {exc}",
        )
    return {
        "symbol": symbol.upper(),
        "patterns": patterns,
        "trend": trend,
    }


@router.get(
    "/{symbol}/support-resistance",
    response_model=dict,
    summary="Calculate support & resistance levels",
)
def support_resistance(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Identify key support and resistance levels for *symbol*."""
    from app.services.pattern_recognition import PatternRecognitionService

    service = PatternRecognitionService()
    try:
        levels = await service.find_support_resistance(symbol=symbol)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S/R calculation failed: {exc}",
        )
    return {
        "symbol": symbol.upper(),
        "support_levels": levels.get("support", []),
        "resistance_levels": levels.get("resistance", []),
    }
