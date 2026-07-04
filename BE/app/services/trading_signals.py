"""
Trading signal generator.
Combines technical indicator signals with ML prediction scores.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import MarketSignal, SignalType
from sqlalchemy import desc

logger = logging.getLogger(__name__)


class TradingSignalGenerator:

    @staticmethod
    def combine_signals(indicator_signals: Dict,
                        ml_score: float = 0.5,
                        threshold: float = 0.55) -> Dict:
        """
        indicator_signals: output of technical_analysis_service._generate_signals()
        ml_score: 0-1 probability (0.5 = neutral)
        """
        score   = 0.0
        reasons = []

        # ML component — 40 %
        if ml_score > threshold:
            score   += 0.40
            reasons.append(f"ML model bullish (score={ml_score:.2f})")
        elif ml_score < (1 - threshold):
            score   -= 0.40
            reasons.append(f"ML model bearish (score={ml_score:.2f})")

        # Indicator component — 60 %
        buys  = len(indicator_signals.get("buy_signals",  []))
        sells = len(indicator_signals.get("sell_signals", []))

        if buys > sells:
            score   += 0.30 * min(buys / max(sells, 1), 2.0) / 2.0
            reasons.append(f"{buys} bullish indicator signals")
        elif sells > buys:
            score   -= 0.30 * min(sells / max(buys, 1), 2.0) / 2.0
            reasons.append(f"{sells} bearish indicator signals")

        score = max(-1.0, min(1.0, score))

        if score > 0.2:
            sig_type = SignalType.BUY.value
        elif score < -0.2:
            sig_type = SignalType.SELL.value
        else:
            sig_type = SignalType.HOLD.value

        return {
            "signal_type": sig_type,
            "strength":    round(score, 3),
            "confidence":  round(abs(score), 3),
            "ml_score":    round(ml_score, 3),
            "reasons":     reasons,
            "buy_count":   buys,
            "sell_count":  sells,
        }

    @staticmethod
    def store_signal(symbol: str, signal_data: Dict) -> bool:
        db = SessionLocal()
        try:
            sig = MarketSignal(
                symbol          = symbol,
                signal_type     = signal_data["signal_type"],
                strength        = signal_data["strength"],
                indicators_used = signal_data.get("reasons"),
                confidence_score= signal_data["confidence"],
                reason          = {
                    "ml_score":   signal_data.get("ml_score"),
                    "buy_count":  signal_data.get("buy_count"),
                    "sell_count": signal_data.get("sell_count"),
                },
            )
            db.add(sig)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing signal for {symbol}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_latest_signal(symbol: str) -> Optional[Dict]:
        db = SessionLocal()
        try:
            sig = (
                db.query(MarketSignal)
                  .filter(MarketSignal.symbol == symbol)
                  .order_by(desc(MarketSignal.timestamp))
                  .first()
            )
            if not sig:
                return None
            return {
                "symbol":          symbol,
                "signal_type":     sig.signal_type.value if hasattr(sig.signal_type, "value") else sig.signal_type,
                "strength":        sig.strength,
                "confidence_score": sig.confidence_score,
                "timestamp":       sig.timestamp.isoformat() if sig.timestamp else None,
            }
        finally:
            db.close()


trading_signal_generator = TradingSignalGenerator()
