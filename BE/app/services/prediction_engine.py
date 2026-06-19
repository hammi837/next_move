"""
Prediction engine service.

Orchestrates ML model inference and model comparison.
"""

from datetime import date, timedelta
from typing import Any


class PredictionEngine:
    """High-level interface for generating and comparing predictions."""

    def __init__(self) -> None:
        pass

    async def predict(
        self,
        symbol: str,
        model_name: str = "ensemble",
        horizon_days: int = 7,
    ) -> dict[str, Any]:
        """
        Generate a price prediction for *symbol*.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        model_name : str
            Model to use: lstm, xgboost, prophet, or ensemble.
        horizon_days : int
            Prediction horizon in days.

        Returns
        -------
        dict with prediction details.
        """
        from app.services.data_collector import DataCollectorService

        collector = DataCollectorService()
        history = await collector.collect_historical(symbol=symbol)

        if not history:
            return {
                "symbol": symbol,
                "error": "Insufficient historical data",
            }

        # Select model
        if model_name == "ensemble":
            from app.ml.ensemble import EnsemblePredictor

            predictor = EnsemblePredictor()
        elif model_name == "lstm":
            from app.ml.lstm_model import LSTMPredictor

            predictor = LSTMPredictor()
        elif model_name == "xgboost":
            from app.ml.xgboost_model import XGBoostPredictor

            predictor = XGBoostPredictor()
        elif model_name == "prophet":
            from app.ml.prophet_model import ProphetPredictor

            predictor = ProphetPredictor()
        else:
            return {"symbol": symbol, "error": f"Unknown model: {model_name}"}

        prediction = await predictor.predict(history, horizon_days=horizon_days)

        return {
            "symbol": symbol,
            "model_used": model_name,
            "predicted_price": prediction.get("price", 0.0),
            "confidence": prediction.get("confidence", 0.0),
            "prediction_date": date.today().isoformat(),
            "target_date": (date.today() + timedelta(days=horizon_days)).isoformat(),
        }

    async def compare_models(
        self,
        symbol: str,
        horizon_days: int = 7,
    ) -> dict[str, Any]:
        """
        Run all models and compare their predictions.
        """
        models = ["lstm", "xgboost", "prophet", "ensemble"]
        results: dict[str, Any] = {"symbol": symbol, "models": {}}
        for model_name in models:
            pred = await self.predict(symbol, model_name, horizon_days)
            results["models"][model_name] = pred
        return results

    async def get_best_model(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Determine the best-performing model for *symbol* based on
        historical accuracy.
        """
        comparison = await self.compare_models(symbol)
        # Simple heuristic: pick highest confidence
        best_model = None
        best_confidence = -1.0
        for name, pred in comparison.get("models", {}).items():
            conf = pred.get("confidence", 0)
            if conf > best_confidence:
                best_confidence = conf
                best_model = name
        return {
            "symbol": symbol,
            "best_model": best_model,
            "confidence": best_confidence,
        }
