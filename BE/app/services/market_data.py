import httpx
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import logging
import concurrent.futures

from app.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

YFINANCE_TIMEOUT = 10  # seconds — fail fast instead of hanging


def _yf_fetch_with_timeout(ticker_symbol: str, **kwargs):
    """Run a yfinance history call with a hard timeout."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(yf.Ticker(ticker_symbol).history, **kwargs)
        try:
            return future.result(timeout=YFINANCE_TIMEOUT)
        except concurrent.futures.TimeoutError:
            logger.error(f"yfinance timeout for {ticker_symbol} after {YFINANCE_TIMEOUT}s")
            return None


class MarketDataService:
    """Fetch market data from various sources."""

    def __init__(self):
        self.alpha_vantage_url = settings.ALPHA_VANTAGE_URL
        self.api_key = settings.ALPHA_VANTAGE_KEY
        self.timeout = httpx.Timeout(30.0)

    # ── Gold Market ────────────────────────────────────────────────────────

    def fetch_gold_price_forex(self) -> Optional[Dict]:
        """Fetch gold price using forex data (XAUUSD/GC=F)."""
        cache_key = "gold_price_current"

        def fetch():
            try:
                data = _yf_fetch_with_timeout("GC=F", period="1d")

                if data is None or data.empty:
                    logger.warning("Empty gold data from yfinance")
                    return None

                latest = data.iloc[-1]
                return {
                    "symbol": "GOLD",
                    "price": float(latest["Close"]),
                    "open": float(latest["Open"]),
                    "high": float(latest["High"]),
                    "low": float(latest["Low"]),
                    "volume": float(latest["Volume"]),
                    "timestamp": data.index[-1].isoformat(),
                    "source": "yfinance",
                }
            except Exception as e:
                logger.error(f"Error fetching gold price: {e}")
                return None

        return cache_service.get_or_set(cache_key, fetch, ex=300)

    def fetch_gold_historical(self, period: str = "1mo", interval: str = "1d") -> Optional[List[Dict]]:
        """Fetch historical gold data."""
        cache_key = f"gold_historical_{period}_{interval}"

        def fetch():
            try:
                data = _yf_fetch_with_timeout("GC=F", period=period, interval=interval)

                if data is None or data.empty:
                    logger.warning(f"Empty gold historical data for {period}")
                    return None

                return data.reset_index().to_dict(orient="records")
            except Exception as e:
                logger.error(f"Error fetching gold historical data: {e}")
                return None

        ttl = 60 if interval != "1d" else 3600
        return cache_service.get_or_set(cache_key, fetch, ex=ttl)

    # ── Stock Market ───────────────────────────────────────────────────────

    def fetch_stock_price(self, symbol: str) -> Optional[Dict]:
        """Fetch current stock price."""
        cache_key = f"stock_price_{symbol.upper()}"

        def fetch():
            try:
                data = _yf_fetch_with_timeout(symbol, period="1d")

                if data is None or data.empty:
                    logger.warning(f"Empty stock data for {symbol}")
                    return None

                latest = data.iloc[-1]
                return {
                    "symbol": symbol.upper(),
                    "price": float(latest["Close"]),
                    "open": float(latest["Open"]),
                    "high": float(latest["High"]),
                    "low": float(latest["Low"]),
                    "volume": float(latest["Volume"]),
                    "timestamp": data.index[-1].isoformat(),
                    "source": "yfinance",
                }
            except Exception as e:
                logger.error(f"Error fetching stock price for {symbol}: {e}")
                return None

        return cache_service.get_or_set(cache_key, fetch, ex=300)

    def fetch_stock_historical(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> Optional[List[Dict]]:
        """Fetch historical stock data."""
        cache_key = f"stock_historical_{symbol.upper()}_{period}_{interval}"

        def fetch():
            try:
                data = _yf_fetch_with_timeout(symbol, period=period, interval=interval)

                if data is None or data.empty:
                    logger.warning(f"Empty historical data for {symbol}")
                    return None

                return data.reset_index().to_dict(orient="records")
            except Exception as e:
                logger.error(f"Error fetching stock historical: {e}")
                return None

        return cache_service.get_or_set(cache_key, fetch, ex=3600)

    # ── Commodities ────────────────────────────────────────────────────────

    def fetch_commodity_price(self, symbol: str) -> Optional[Dict]:
        """Fetch commodity prices."""
        commodity_symbols = {
            "crude_oil": "CL=F",
            "natural_gas": "NG=F",
            "copper": "HG=F",
            "silver": "SI=F",
            "platinum": "PL=F",
        }

        ticker = commodity_symbols.get(symbol.lower())
        if not ticker:
            logger.warning(f"Unknown commodity: {symbol}")
            return None

        cache_key = f"commodity_{symbol.lower()}_price"

        def fetch():
            try:
                data = _yf_fetch_with_timeout(ticker, period="1d")

                if data is None or data.empty:
                    return None

                latest = data.iloc[-1]
                return {
                    "symbol": symbol.upper(),
                    "ticker": ticker,
                    "price": float(latest["Close"]),
                    "open": float(latest["Open"]),
                    "high": float(latest["High"]),
                    "low": float(latest["Low"]),
                    "volume": float(latest["Volume"]),
                    "timestamp": data.index[-1].isoformat(),
                }
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                return None

        return cache_service.get_or_set(cache_key, fetch, ex=300)

    # ── Utilities ──────────────────────────────────────────────────────────

    def format_for_storage(self, symbol: str, data: Dict, market_type: str) -> Dict:
        """Format API data for database storage."""
        ts_str = data.get("timestamp")
        if isinstance(ts_str, pd.Timestamp):
            ts = ts_str.to_pydatetime()
        elif ts_str:
            ts = datetime.fromisoformat(str(ts_str))
        else:
            ts = datetime.utcnow()

        # strip timezone info since SQLAlchemy expects naive datetime or timezone aware depending on DB
        if ts.tzinfo is not None:
             ts = ts.replace(tzinfo=None)

        return {
            "symbol": symbol,
            "market_type": market_type,
            "open_price": data.get("open"),
            "high_price": data.get("high"),
            "low_price": data.get("low"),
            "close_price": data.get("price") or data.get("Close"),
            "volume": data.get("volume") or data.get("Volume"),
            "timestamp": ts,
        }


# Singleton instance
market_data_service = MarketDataService()
