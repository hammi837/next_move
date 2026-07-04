"""
Phase 3 — ML Predictions API.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
import logging

from app.db.database import get_db
from app.services.prediction_engine  import prediction_engine
from app.services.data_preparation   import data_preparation_service
from app.services.backtesting        import BacktestingEngine
from app.services.trading_signals    import trading_signal_generator
from app.services.technical_analysis import technical_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()

SYMBOLS = ["GOLD", "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]


# ── Price forecast ────────────────────────────────────────────────────────

@router.get("/{symbol}/predict")
def predict_future_price(
    symbol: str,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Predict future prices (7-day default) for a symbol."""
    symbol = symbol.upper()
    if not prediction_engine.model_exists(symbol):
        raise HTTPException(
            status_code=404,
            detail=f"No model for {symbol}. POST /{symbol}/train-model first.",
        )
    result = prediction_engine.predict_future(symbol, days)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


# ── Model training ────────────────────────────────────────────────────────

@router.post("/{symbol}/train-model")
def train_model(
    symbol: str,
    epochs: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db),
):
    """
    Train the ensemble ML model for a symbol.
    Requires at least 60 rows of price history in the DB.
    `epochs` is accepted for API compatibility but ignored by sklearn models.
    """
    symbol = symbol.upper()
    logger.info(f"Training model for {symbol}…")
    result = prediction_engine.train(symbol, epochs=epochs)
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("error"))
    return result


# ── Model performance ─────────────────────────────────────────────────────

@router.get("/{symbol}/model-performance")
def get_model_performance(symbol: str, db: Session = Depends(get_db)):
    """Return evaluation metrics for the trained model on its test set."""
    symbol = symbol.upper()
    if not prediction_engine.model_exists(symbol):
        raise HTTPException(
            status_code=404,
            detail=f"No model for {symbol}. Train it first.",
        )
    result = prediction_engine.get_performance(symbol)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return {"symbol": symbol, "model_metrics": result["metrics"],
            "last_updated": datetime.utcnow().isoformat()}


# ── Trading signal ────────────────────────────────────────────────────────

@router.get("/{symbol}/trading-signal")
def get_trading_signal(symbol: str, db: Session = Depends(get_db)):
    """
    Combined trading signal — technical indicators + ML prediction.
    If no model is trained, ml_score defaults to 0.5 (neutral).
    """
    symbol = symbol.upper()

    indicators = technical_analysis_service.calculate_all_indicators(symbol)
    if not indicators:
        raise HTTPException(status_code=503, detail="Unable to calculate indicators")

    # ML score (0 = very bearish, 1 = very bullish, 0.5 = neutral)
    ml_score = 0.5
    if prediction_engine.model_exists(symbol):
        try:
            data = data_preparation_service.prepare_data(symbol, days=120)
            if "error" not in data and len(data["X_test"]) > 0:
                X_last = data["X_test"][[-1]]
                X_flat = X_last.reshape(1, -1)
                ridge, gbr = prediction_engine._load_models(symbol)
                raw  = prediction_engine._ensemble_predict(ridge, gbr, X_flat)[0]
                # Normalise to 0–1 via sigmoid-like mapping
                ml_score = float(1 / (1 + np.exp(-10 * (raw - 0.5))))
        except Exception as e:
            logger.warning(f"ML score failed for {symbol}: {e}")

    signal = trading_signal_generator.combine_signals(
        indicators.get("signals", {}), ml_score
    )
    trading_signal_generator.store_signal(symbol, signal)

    return {
        "symbol":         symbol,
        "trading_signal": signal,
        "timestamp":      datetime.utcnow().isoformat(),
    }


# ── Backtesting ───────────────────────────────────────────────────────────

@router.post("/{symbol}/backtest")
def run_backtest(
    symbol:          str,
    initial_capital: float = Query(10_000, ge=100),
    days:            int   = Query(90, ge=30, le=365),
    db: Session = Depends(get_db),
):
    """
    Run a backtest on historical price data using the trained model's signals.
    """
    symbol = symbol.upper()

    # Fetch real prices from DB for the period
    from app.db.database import SessionLocal
    from app.db.models   import PriceHistory
    from datetime        import timedelta
    from sqlalchemy      import asc

    sess  = SessionLocal()
    start = datetime.utcnow() - timedelta(days=days)
    rows  = (
        sess.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol,
                    PriceHistory.timestamp >= start)
            .order_by(asc(PriceHistory.timestamp))
            .all()
    )
    sess.close()

    if len(rows) < 10:
        raise HTTPException(status_code=404,
                            detail=f"Not enough history for {symbol} ({len(rows)} rows)")

    prices = np.array([r.close_price for r in rows if r.close_price], dtype=float)
    dates  = [r.timestamp for r in rows if r.close_price]

    if prediction_engine.model_exists(symbol):
        try:
            data = data_preparation_service.prepare_data(symbol, days=days)
            if "error" not in data and len(data["X_test"]) > 0:
                ridge, gbr = prediction_engine._load_models(symbol)
                X_flat  = data_preparation_service.DataPreparationService._flatten(
                    prediction_engine, data["X_test"])
                preds   = prediction_engine._ensemble_predict(ridge, gbr, X_flat)
                # Align preds to price array length
                n = min(len(prices), len(preds))
                prices  = prices[:n]
                dates   = dates[:n]
                signals = BacktestingEngine.signals_from_predictions(preds[:n])
            else:
                signals = BacktestingEngine.signals_from_predictions(
                    _momentum_signals(prices))
        except Exception as e:
            logger.warning(f"Model predict failed in backtest: {e}")
            signals = BacktestingEngine.signals_from_predictions(
                _momentum_signals(prices))
    else:
        # Fallback: pure momentum signals (buy when 5-day slope > 0)
        signals = BacktestingEngine.signals_from_predictions(
            _momentum_signals(prices))

    engine = BacktestingEngine(initial_capital=initial_capital)
    report = engine.run(prices, signals, dates)

    return {
        "symbol":           symbol,
        "period_days":      days,
        "initial_capital":  initial_capital,
        "backtest_results": report,
    }


# ── Latest stored signal ──────────────────────────────────────────────────

@router.get("/{symbol}/latest-signal")
def get_latest_signal(symbol: str, db: Session = Depends(get_db)):
    """Return the most recent stored trading signal for a symbol."""
    symbol = symbol.upper()
    sig    = trading_signal_generator.get_latest_signal(symbol)
    if not sig:
        raise HTTPException(status_code=404, detail=f"No stored signals for {symbol}")
    return sig


# ── Model status overview ─────────────────────────────────────────────────

@router.get("/models/status")
def models_status():
    """Show which symbols have trained models."""
    return {
        "models": {
            sym: prediction_engine.model_exists(sym)
            for sym in SYMBOLS
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Helpers ───────────────────────────────────────────────────────────────

def _momentum_signals(prices: np.ndarray, window: int = 5) -> np.ndarray:
    """Simple momentum: normalised 5-day slope as pseudo-prediction."""
    result = np.zeros(len(prices))
    for i in range(window, len(prices)):
        slope = (prices[i] - prices[i - window]) / prices[i - window]
        # Map slope to 0-1 range (positive slope → > 0.5)
        result[i] = 0.5 + np.tanh(slope * 20) * 0.5
    return result
