"""
Prediction route module.

Endpoints for fetching, generating, and backtesting ML predictions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.prediction import PredictionCreate, PredictionResponse

router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"],
)


@router.get(
    "/{symbol}",
    response_model=dict,
    summary="Get latest prediction for a symbol",
)
def get_prediction(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return the most recent prediction for *symbol*."""
    from app.models.prediction import Prediction

    result = await db.execute(
        select(Prediction)
        .where(Prediction.symbol == symbol.upper())
        .order_by(Prediction.prediction_date.desc())
        .limit(1)
    )
    prediction = result.scalar_one_or_none()
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No predictions found for {symbol}",
        )
    return {
        "id": prediction.id,
        "symbol": prediction.symbol,
        "predicted_price": float(prediction.predicted_price),
        "confidence": float(prediction.confidence),
        "model_used": prediction.model_used,
        "prediction_date": prediction.prediction_date.isoformat(),
        "target_date": prediction.target_date.isoformat(),
        "actual_price": float(prediction.actual_price) if prediction.actual_price else None,
    }


@router.post(
    "/{symbol}/generate",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new prediction",
)
def generate_prediction(
    symbol: str,
    model: str = Query("ensemble", description="Model to use (lstm, xgboost, prophet, ensemble)"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Trigger a new ML prediction for *symbol*."""
    from app.services.prediction_engine import PredictionEngine

    engine = PredictionEngine()
    try:
        prediction = await engine.predict(symbol=symbol.upper(), model_name=model)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction generation failed: {exc}",
        )
    return prediction


@router.get(
    "/{symbol}/backtest",
    response_model=dict,
    summary="Get backtesting results",
)
def get_backtest_results(
    symbol: str,
    model: str = Query("ensemble", description="Model to backtest"),
    days: int = Query(30, ge=7, le=365, description="Number of days to backtest"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Run and return backtesting results for *symbol*."""
    from app.ml.backtester import Backtester

    backtester = Backtester()
    try:
        report = await backtester.run_backtest(
            symbol=symbol.upper(),
            model_name=model,
            days=days,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {exc}",
        )
    return report
