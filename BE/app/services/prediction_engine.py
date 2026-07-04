"""
Prediction engine — lightweight ML using scikit-learn.

Uses an ensemble of:
  1. Ridge regression on flattened sequence features
  2. Gradient-boosted trees (GradientBoostingRegressor)
  3. Simple momentum extrapolation (baseline)

No TensorFlow required. Works with as few as 60 rows of history.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, List, Optional
from datetime import datetime
import logging
import pickle
import os

from app.services.data_preparation import data_preparation_service

logger = logging.getLogger(__name__)

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


def _safe(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 6)
    except Exception:
        return None


class PredictionEngineService:
    """Train, evaluate, and predict with the ensemble model."""

    # ── Model paths ───────────────────────────────────────────────────────

    def _ridge_path(self, symbol: str) -> str:
        return f"{MODEL_DIR}/{symbol}_ridge.pkl"

    def _gbr_path(self, symbol: str) -> str:
        return f"{MODEL_DIR}/{symbol}_gbr.pkl"

    # ── Training ──────────────────────────────────────────────────────────

    def _flatten(self, X: np.ndarray) -> np.ndarray:
        """Flatten (N, T, F) → (N, T*F) for sklearn models."""
        return X.reshape(X.shape[0], -1)

    def train(self, symbol: str, epochs: int = 100) -> Dict:
        """
        Train the ensemble for a symbol.
        `epochs` is ignored here (kept for API compatibility with the plan).
        """
        data = data_preparation_service.prepare_data(symbol, days=365)
        if "error" in data:
            return {"status": "error", "symbol": symbol, "error": data["error"]}

        X_train_f = self._flatten(data["X_train"])
        X_test_f  = self._flatten(data["X_test"])
        y_train   = data["y_train"]
        y_test    = data["y_test"]

        # Ridge regression
        ridge = Ridge(alpha=1.0)
        ridge.fit(X_train_f, y_train)

        # Gradient boosting
        n_est = min(200, max(50, len(X_train_f) // 5))
        gbr   = GradientBoostingRegressor(
            n_estimators=n_est, learning_rate=0.05,
            max_depth=3, subsample=0.8, random_state=42,
        )
        gbr.fit(X_train_f, y_train)

        # Ensemble predictions on test set
        preds = self._ensemble_predict(ridge, gbr, X_test_f)
        metrics = self._compute_metrics(y_test, preds)

        # Save
        with open(self._ridge_path(symbol), "wb") as f:
            pickle.dump(ridge, f)
        with open(self._gbr_path(symbol), "wb") as f:
            pickle.dump(gbr, f)
        data_preparation_service.save_scaler(symbol, data["scaler_params"])

        logger.info(f"✅ Model trained for {symbol} — R²={metrics['r2']:.3f}")
        return {
            "status":        "success",
            "symbol":        symbol,
            "metrics":       metrics,
            "model_path":    self._gbr_path(symbol),
            "timestamp":     datetime.utcnow().isoformat(),
        }

    # ── Loading ───────────────────────────────────────────────────────────

    def _load_models(self, symbol: str):
        """Return (ridge, gbr) or raise FileNotFoundError."""
        rp = self._ridge_path(symbol)
        gp = self._gbr_path(symbol)
        if not os.path.exists(rp) or not os.path.exists(gp):
            raise FileNotFoundError(f"No model found for {symbol}. Train first.")
        with open(rp, "rb") as f:
            ridge = pickle.load(f)
        with open(gp, "rb") as f:
            gbr = pickle.load(f)
        return ridge, gbr

    def model_exists(self, symbol: str) -> bool:
        return (os.path.exists(self._ridge_path(symbol)) and
                os.path.exists(self._gbr_path(symbol)))

    # ── Prediction helpers ────────────────────────────────────────────────

    @staticmethod
    def _ensemble_predict(ridge, gbr, X_flat: np.ndarray) -> np.ndarray:
        p1 = ridge.predict(X_flat)
        p2 = gbr.predict(X_flat)
        return 0.4 * p1 + 0.6 * p2   # GBR weighted slightly higher

    @staticmethod
    def _momentum_extrapolate(last_seq: np.ndarray, days: int,
                              close_col: int = 3) -> np.ndarray:
        """Simple linear extrapolation of normalised close over last 5 bars."""
        window = min(5, last_seq.shape[0])
        recent = last_seq[-window:, close_col]
        slope  = (recent[-1] - recent[0]) / max(window - 1, 1)
        return np.array([recent[-1] + slope * (i + 1) for i in range(days)])

    # ── Public prediction methods ─────────────────────────────────────────

    def predict_test_set(self, symbol: str) -> Dict:
        """Predictions on the held-out test portion (for evaluation)."""
        ridge, gbr = self._load_models(symbol)
        data = data_preparation_service.prepare_data(symbol, days=365)
        if "error" in data:
            return {"error": data["error"]}

        X_test_f = self._flatten(data["X_test"])
        preds    = self._ensemble_predict(ridge, gbr, X_test_f)
        metrics  = self._compute_metrics(data["y_test"], preds)
        return {"symbol": symbol, "metrics": metrics,
                "predictions": preds.tolist(),
                "actuals":     data["y_test"].tolist()}

    def predict_future(self, symbol: str, days: int = 7) -> Dict:
        """
        Predict `days` future normalised close prices,
        then denormalise back to USD.
        """
        ridge, gbr   = self._load_models(symbol)
        scaler_params = data_preparation_service.load_scaler(symbol)
        data          = data_preparation_service.prepare_data(symbol, days=120)
        if "error" in data:
            return {"error": data["error"]}

        # Use the very last sequence from the test set as seed
        if len(data["X_test"]) == 0 and len(data["X_train"]) == 0:
            return {"error": "No sequences available"}

        last_seq = (data["X_test"][-1] if len(data["X_test"]) > 0
                    else data["X_train"][-1])   # (T, F)

        # Momentum baseline
        momentum = self._momentum_extrapolate(last_seq, days)

        # Model-based: roll the window forward
        current = last_seq.copy()
        model_preds = []
        for _ in range(days):
            X_flat   = self._flatten(current[np.newaxis])
            norm_pred = self._ensemble_predict(ridge, gbr, X_flat)[0]
            model_preds.append(norm_pred)
            # Slide window: drop oldest, append new row (update close col)
            new_row          = current[-1].copy()
            new_row[3]       = norm_pred   # close col
            current          = np.vstack([current[1:], new_row])

        # Blend model + momentum
        blended = [0.7 * mp + 0.3 * mo
                   for mp, mo in zip(model_preds, momentum)]

        # Denormalise
        if scaler_params:
            prices = [data_preparation_service.denormalize_close(v, scaler_params)
                      for v in blended]
        else:
            prices = blended   # return normalised if scaler unavailable

        # Confidence decays with horizon
        confidences = [round(max(0.40, 0.80 - 0.06 * i), 2) for i in range(days)]

        # Date labels
        today = datetime.utcnow().date()
        labels = []
        d = today
        for _ in range(days):
            from datetime import date as _date
            import datetime as _dt
            d += _dt.timedelta(days=1)
            while d.weekday() >= 5:   # skip weekends
                d += _dt.timedelta(days=1)
            labels.append(str(d))

        return {
            "symbol":       symbol,
            "forecast_days": days,
            "predictions":  [round(float(p), 2) for p in prices],
            "confidences":  confidences,
            "dates":        labels,
            "timestamp":    datetime.utcnow().isoformat(),
        }

    # ── Metrics ───────────────────────────────────────────────────────────

    @staticmethod
    def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        mse  = mean_squared_error(y_true, y_pred)
        mae  = mean_absolute_error(y_true, y_pred)
        r2   = r2_score(y_true, y_pred)
        rmse = float(np.sqrt(mse))
        mape = float(np.mean(np.abs((y_true - y_pred) /
                                    np.where(y_true != 0, y_true, 1e-9))) * 100)

        # Directional accuracy
        da = 0.0
        if len(y_true) > 1:
            true_dir = np.sign(np.diff(y_true))
            pred_dir = np.sign(np.diff(y_pred))
            da = float(np.mean(true_dir == pred_dir) * 100)

        return {
            "mse":  _safe(mse),
            "rmse": _safe(rmse),
            "mae":  _safe(mae),
            "r2":   _safe(r2),
            "mape": _safe(mape),
            "directional_accuracy": round(da, 2),
        }

    def get_performance(self, symbol: str) -> Dict:
        """Return metrics for the trained model on the test set."""
        if not self.model_exists(symbol):
            return {"error": f"No model for {symbol}. Train first."}
        return self.predict_test_set(symbol)


# Singleton
prediction_engine = PredictionEngineService()
