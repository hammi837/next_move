"""
Backtesting engine.
Simulates trading on historical data using model-generated signals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    BUY  = "buy"
    SELL = "sell"
    HOLD = "hold"


class Trade:
    def __init__(self, entry_price: float, entry_date, signal: str):
        self.entry_price = entry_price
        self.entry_date  = entry_date
        self.signal      = signal
        self.exit_price: Optional[float] = None
        self.exit_date   = None

    @property
    def is_closed(self) -> bool:
        return self.exit_price is not None

    @property
    def profit_loss(self) -> float:
        return (self.exit_price - self.entry_price) if self.is_closed else 0.0

    @property
    def pnl_pct(self) -> float:
        return (self.profit_loss / self.entry_price * 100) if self.entry_price else 0.0


class BacktestingEngine:
    """Event-driven backtester with portfolio tracking."""

    def __init__(self, initial_capital: float = 10_000,
                 commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission      = commission
        self._reset()

    def _reset(self):
        self.cash             = self.initial_capital
        self.position: Optional[Trade] = None
        self.trades:   List[Trade] = []
        self.portfolio_values: List[float] = []

    # ── Signal generation from predictions ───────────────────────────────

    @staticmethod
    def signals_from_predictions(predictions: np.ndarray,
                                  threshold: float = 0.002) -> List[OrderType]:
        """
        Convert normalised prediction array → BUY/SELL/HOLD list.
        `threshold`: minimum fractional move to trigger a trade.
        """
        signals = []
        for i in range(len(predictions) - 1):
            delta = predictions[i + 1] - predictions[i]
            if delta > threshold:
                signals.append(OrderType.BUY)
            elif delta < -threshold:
                signals.append(OrderType.SELL)
            else:
                signals.append(OrderType.HOLD)
        signals.append(OrderType.HOLD)  # last bar — no trade
        return signals

    # ── Execution ─────────────────────────────────────────────────────────

    def _open(self, price: float, date, signal: str):
        cost = price * (1 + self.commission)
        if cost <= self.cash:
            self.position = Trade(price, date, signal)
            self.cash    -= cost

    def _close(self, price: float, date):
        if self.position is None:
            return
        self.position.exit_price = price
        self.position.exit_date  = date
        self.cash += price * (1 - self.commission)
        self.trades.append(self.position)
        self.position = None

    def run(self, prices: np.ndarray,
            signals: List[OrderType],
            dates: Optional[List] = None) -> Dict:
        self._reset()
        if dates is None:
            dates = list(range(len(prices)))

        for price, signal, date in zip(prices, signals, dates):
            # Mark-to-market portfolio value
            pv = self.cash + (price if self.position else 0)
            self.portfolio_values.append(float(pv))

            if signal == OrderType.BUY and self.position is None:
                self._open(float(price), date, "buy")
            elif signal == OrderType.SELL and self.position is not None:
                self._close(float(price), date)

        # Close any open position at end of period
        if self.position is not None:
            self._close(float(prices[-1]), dates[-1])

        return self._report()

    # ── Reporting ─────────────────────────────────────────────────────────

    def _report(self) -> Dict:
        if not self.trades:
            return {
                "initial_capital":     self.initial_capital,
                "final_value":         float(self.cash),
                "total_return_percent": 0.0,
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
                "profit_factor": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0,
                "note": "No trades were executed",
            }

        pnls = [t.profit_loss for t in self.trades]
        wins = [p for p in pnls if p > 0]
        loss = [p for p in pnls if p < 0]

        final   = self.portfolio_values[-1] if self.portfolio_values else self.cash
        ret_pct = (final - self.initial_capital) / self.initial_capital * 100
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0

        avg_win  = float(np.mean(wins)) if wins else 0.0
        avg_loss = float(np.mean(loss)) if loss else 0.0
        pf = abs(avg_win * len(wins) / (avg_loss * len(loss))) if loss and avg_loss != 0 else float("inf")

        return {
            "initial_capital":       self.initial_capital,
            "final_value":           round(float(final), 2),
            "total_return_percent":  round(float(ret_pct), 2),
            "total_trades":          len(self.trades),
            "winning_trades":        len(wins),
            "losing_trades":         len(loss),
            "win_rate":              round(win_rate, 2),
            "avg_win":               round(avg_win, 4),
            "avg_loss":              round(avg_loss, 4),
            "profit_factor":         round(min(pf, 99.0), 2),
            "max_drawdown":          round(self._max_drawdown(), 2),
            "sharpe_ratio":          round(self._sharpe(), 2),
            "trades": [
                {"entry": t.entry_price, "exit": t.exit_price,
                 "pnl": round(t.profit_loss, 4),
                 "pnl_pct": round(t.pnl_pct, 2)}
                for t in self.trades
            ],
        }

    def _max_drawdown(self) -> float:
        if len(self.portfolio_values) < 2:
            return 0.0
        arr = np.array(self.portfolio_values)
        peak = np.maximum.accumulate(arr)
        dd   = (arr - peak) / np.where(peak != 0, peak, 1)
        return float(np.min(dd) * 100)

    def _sharpe(self, rf: float = 0.02) -> float:
        if len(self.portfolio_values) < 2:
            return 0.0
        rets = np.diff(self.portfolio_values) / np.array(self.portfolio_values[:-1])
        mu   = np.mean(rets) - rf / 252
        std  = np.std(rets)
        return float(mu / std * np.sqrt(252)) if std > 0 else 0.0
