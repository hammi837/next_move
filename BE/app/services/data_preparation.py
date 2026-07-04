"""
Data preparation service for ML models.
Fetches price history from DB, engineers features, normalises, and creates sequences.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import os

from app.db.database import SessionLocal
from app.db.models import PriceHistory

logger = logging.getLogger(__name__)

SEQUENCE_LENGTH = 30   # lookback window (days)
TEST_SPLIT      = 0.2
MIN_RECORDS     = 60   # minimum rows needed


class DataPreparationService:
    """Prepare and normalise OHLCV data for ML models."""

    def __init__(self):
        self.scaler          = MinMaxScaler(feature_range=(0, 1))
        self.sequence_length = SEQUENCE_LENGTH
        self.test_split      = TEST_SPLIT

    # ── Fetching ──────────────────────────────────────────────────────────

    @staticmethod
    def fetch_training_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        db = SessionLocal()
        try:
            start = datetime.utcnow() - timedelta(days=days)
            rows  = (
                db.query(PriceHistory)
                  .filter(PriceHistory.symbol == symbol,
                          PriceHistory.timestamp >= start)
                  .order_by(PriceHistory.timestamp)
                  .all()
            )
            if len(rows) < MIN_RECORDS:
                logger.warning(f"Insufficient data for {symbol}: {len(rows)} rows")
                return None

            return pd.DataFrame({
                "timestamp": [r.timestamp   for r in rows],
                "open":      [r.open_price  or 0.0 for r in rows],
                "high":      [r.high_price  or 0.0 for r in rows],
                "low":       [r.low_price   or 0.0 for r in rows],
                "close":     [r.close_price or 0.0 for r in rows],
                "volume":    [r.volume      or 0.0 for r in rows],
            })
        finally:
            db.close()

    # ── Cleaning ──────────────────────────────────────────────────────────

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()
        df = df[df["close"] > 0]
        # Replace zero volume with mean
        mean_vol = df["volume"].replace(0, np.nan).mean()
        df["volume"] = df["volume"].replace(0, mean_vol)
        # Drop extreme outliers (>15% single-bar move)
        pct = df["close"].pct_change().abs()
        df  = df[pct.fillna(0) < 0.15]
        return df.reset_index(drop=True)

    # ── Feature engineering ───────────────────────────────────────────────

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        d["returns"]          = d["close"].pct_change()
        d["hl_ratio"]         = d["high"] / d["low"].replace(0, np.nan)
        d["co_ratio"]         = d["close"] / d["open"].replace(0, np.nan)
        d["vol_ma_ratio"]     = d["volume"] / d["volume"].rolling(10).mean()
        d["sma_10"]           = d["close"].rolling(10).mean()
        d["sma_20"]           = d["close"].rolling(20).mean()
        d["ema_12"]           = d["close"].ewm(span=12, adjust=False).mean()
        d["momentum"]         = d["close"].diff(5)
        d["volatility"]       = d["returns"].rolling(10).std()

        # RSI
        delta = d["close"].diff()
        gain  = delta.clip(lower=0)
        loss  = -delta.clip(upper=0)
        avg_g = gain.ewm(com=13, min_periods=14).mean()
        avg_l = loss.ewm(com=13, min_periods=14).mean()
        rs    = avg_g / avg_l.replace(0, np.nan)
        d["rsi"] = 100 - (100 / (1 + rs))

        d = d.drop(columns=["timestamp"], errors="ignore")
        return d.dropna().reset_index(drop=True)

    # ── Normalisation ─────────────────────────────────────────────────────

    def normalize_data(self, df: pd.DataFrame, fit: bool = True) -> Tuple[pd.DataFrame, Dict]:
        cols = df.columns.tolist()
        if fit:
            arr = self.scaler.fit_transform(df[cols])
        else:
            arr = self.scaler.transform(df[cols])

        params = {
            "feature_min":   self.scaler.data_min_.tolist(),
            "feature_max":   self.scaler.data_max_.tolist(),
            "feature_names": cols,
        }
        return pd.DataFrame(arr, columns=cols), params

    def denormalize_close(self, normalized_val: float, scaler_params: Dict) -> float:
        """Inverse-transform a normalised close price."""
        names = scaler_params["feature_names"]
        if "close" not in names:
            return normalized_val
        idx  = names.index("close")
        lo   = scaler_params["feature_min"][idx]
        hi   = scaler_params["feature_max"][idx]
        return float(normalized_val * (hi - lo) + lo)

    # ── Sequence creation ─────────────────────────────────────────────────

    def create_sequences(self, data: np.ndarray,
                         target_col: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i : i + self.sequence_length, :])
            y.append(data[i + self.sequence_length, target_col])
        return np.array(X), np.array(y)

    # ── Train / test split ────────────────────────────────────────────────

    def train_test_split(self, X: np.ndarray, y: np.ndarray):
        split = int(len(X) * (1 - self.test_split))
        return X[:split], X[split:], y[:split], y[split:]

    # ── Complete pipeline ─────────────────────────────────────────────────

    def prepare_data(self, symbol: str, days: int = 365) -> Dict:
        df = self.fetch_training_data(symbol, days)
        if df is None:
            return {"error": "Insufficient data"}

        df = self.clean_data(df)
        df = self.create_features(df)

        if len(df) < self.sequence_length + 10:
            return {"error": "Not enough clean data after feature engineering"}

        df_norm, scaler_params = self.normalize_data(df, fit=True)
        X, y = self.create_sequences(df_norm.values)
        X_train, X_test, y_train, y_test = self.train_test_split(X, y)

        return {
            "X_train":        X_train,
            "X_test":         X_test,
            "y_train":        y_train,
            "y_test":         y_test,
            "scaler_params":  scaler_params,
            "feature_columns": df_norm.columns.tolist(),
            "sequence_length": self.sequence_length,
            "symbol":          symbol,
        }

    # ── Scaler persistence ────────────────────────────────────────────────

    def save_scaler(self, symbol: str, params: Dict):
        os.makedirs("models", exist_ok=True)
        with open(f"models/{symbol}_scaler.pkl", "wb") as f:
            pickle.dump(params, f)

    def load_scaler(self, symbol: str) -> Optional[Dict]:
        path = f"models/{symbol}_scaler.pkl"
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)


# Singleton
data_preparation_service = DataPreparationService()
