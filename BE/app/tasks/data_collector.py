from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
import logging
from typing import List
from functools import partial

from app.config import settings
from app.services.market_data import market_data_service
from app.db.database import SessionLocal
from app.db.models import PriceHistory, MarketMetadata, MarketType, DataSyncLog

logger = logging.getLogger(__name__)


class DataCollector:
    """Background data collection service."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    # ── Gold ──────────────────────────────────────────────────────────────

    async def collect_gold_data(self):
        """Collect gold price data periodically."""
        db = SessionLocal()
        try:
            logger.info("📊 Collecting gold data...")
            loop = asyncio.get_event_loop()
            gold_data = await loop.run_in_executor(
                None, market_data_service.fetch_gold_price_forex
            )
            if not gold_data:
                logger.warning("Failed to fetch gold data")
                self._log_sync(db, "GOLD", "fetch", "failure", error="Empty response")
                return

            formatted = market_data_service.format_for_storage("GOLD", gold_data, "gold")
            db.add(PriceHistory(**formatted))

            # Upsert metadata
            meta = db.query(MarketMetadata).filter_by(symbol="GOLD").first()
            if not meta:
                meta = MarketMetadata(
                    symbol="GOLD",
                    market_type=MarketType.GOLD,
                    name="Gold",
                    last_price=gold_data["price"],
                    last_update=datetime.utcnow(),
                )
                db.add(meta)
            else:
                meta.last_price = gold_data["price"]
                meta.last_update = datetime.utcnow()

            db.commit()
            logger.info(f"✅ Gold data collected: ${gold_data['price']}")
            self._log_sync(db, "GOLD", "store", "success", count=1)
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error collecting gold data: {e}")
            self._log_sync(db, "GOLD", "collect", "failure", error=str(e))
        finally:
            db.close()

    # ── Stocks ────────────────────────────────────────────────────────────

    async def collect_stock_data(self, symbols: List[str] = None):
        """Collect stock data periodically."""
        if symbols is None:
            symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

        db = SessionLocal()
        try:
            logger.info(f"📊 Collecting stock data for {len(symbols)} symbols...")
            collected = 0

            for symbol in symbols:
                loop = asyncio.get_event_loop()
                stock_data = await loop.run_in_executor(
                    None, partial(market_data_service.fetch_stock_price, symbol)
                )
                if not stock_data:
                    logger.warning(f"Failed to fetch data for {symbol}")
                    continue

                formatted = market_data_service.format_for_storage(symbol, stock_data, "stock")
                db.add(PriceHistory(**formatted))

                meta = db.query(MarketMetadata).filter_by(symbol=symbol).first()
                if not meta:
                    meta = MarketMetadata(
                        symbol=symbol,
                        market_type=MarketType.STOCK,
                        name=symbol,
                        last_price=stock_data["price"],
                        last_update=datetime.utcnow(),
                    )
                    db.add(meta)
                else:
                    meta.last_price = stock_data["price"]
                    meta.last_update = datetime.utcnow()

                collected += 1

            db.commit()
            logger.info(f"✅ Stock data collected for {collected} symbols")
            self._log_sync(db, "STOCKS", "store", "success", count=collected)
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error collecting stock data: {e}")
            self._log_sync(db, "STOCKS", "collect", "failure", error=str(e))
        finally:
            db.close()

    # ── Commodities ───────────────────────────────────────────────────────

    async def collect_commodity_data(self, commodities: List[str] = None):
        """Collect commodity data."""
        if commodities is None:
            commodities = ["crude_oil", "natural_gas", "copper", "silver"]

        db = SessionLocal()
        try:
            logger.info("📊 Collecting commodity data...")
            collected = 0

            for commodity in commodities:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None, partial(market_data_service.fetch_commodity_price, commodity)
                )
                if not data:
                    continue

                formatted = market_data_service.format_for_storage(
                    commodity.upper(), data, "commodity"
                )
                db.add(PriceHistory(**formatted))
                collected += 1

            db.commit()
            logger.info(f"✅ Commodity data collected: {collected}")
            self._log_sync(db, "COMMODITIES", "store", "success", count=collected)
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error collecting commodity data: {e}")
        finally:
            db.close()

    # ── Historical seed (runs once on boot if DB is sparse) ───────────────

    async def seed_historical_data(self):
        """Seed 7 days of daily history for all symbols if the DB has < 2 distinct days."""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            from app.db.models import PriceHistory as PH

            symbols_to_seed = []

            # Gold
            gold_days = db.query(func.count(func.distinct(
                func.date_trunc('day', PH.timestamp)
            ))).filter(PH.symbol == "GOLD").scalar() or 0
            if gold_days < 2:
                symbols_to_seed.append(("GOLD", "gold"))

            # Stocks
            for sym in ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]:
                stock_days = db.query(func.count(func.distinct(
                    func.date_trunc('day', PH.timestamp)
                ))).filter(PH.symbol == sym).scalar() or 0
                if stock_days < 2:
                    symbols_to_seed.append((sym, "stock"))

            if not symbols_to_seed:
                logger.info("✅ Historical data already seeded, skipping.")
                return

            logger.info(f"🌱 Seeding 7-day history for: {[s[0] for s in symbols_to_seed]}")
            loop = asyncio.get_event_loop()

            for symbol, market_type in symbols_to_seed:
                try:
                    if symbol == "GOLD":
                        historical = await loop.run_in_executor(
                            None, partial(market_data_service.fetch_gold_historical, "7d", "1d")
                        )
                        mtype = MarketType.GOLD
                    else:
                        historical = await loop.run_in_executor(
                            None, partial(market_data_service.fetch_stock_historical, symbol, "7d", "1d")
                        )
                        mtype = MarketType.STOCK

                    if not historical:
                        continue

                    for rec in historical:
                        ts = rec.get("Date") or rec.get("Datetime")
                        if ts is None:
                            continue
                        if hasattr(ts, 'to_pydatetime'):
                            ts = ts.to_pydatetime().replace(tzinfo=None)
                        elif hasattr(ts, 'tzinfo') and ts.tzinfo:
                            ts = ts.replace(tzinfo=None)

                        # Skip if already exists for this day
                        exists = db.query(PriceHistory).filter(
                            PriceHistory.symbol == symbol,
                            func.date_trunc('day', PriceHistory.timestamp) == func.date_trunc('day', ts)
                        ).first()
                        if exists:
                            continue

                        db.add(PriceHistory(
                            symbol=symbol,
                            market_type=mtype,
                            open_price=rec.get("Open"),
                            high_price=rec.get("High"),
                            low_price=rec.get("Low"),
                            close_price=rec.get("Close"),
                            volume=rec.get("Volume"),
                            timestamp=ts,
                        ))

                    db.commit()
                    logger.info(f"✅ Seeded history for {symbol}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"❌ Failed to seed {symbol}: {e}")

        except Exception as e:
            logger.error(f"❌ Historical seed failed: {e}")
        finally:
            db.close()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _log_sync(self, db, symbol, operation, status, count=None, error=None):
        try:
            db.add(
                DataSyncLog(
                    symbol=symbol,
                    operation=operation,
                    status=status,
                    record_count=count,
                    error_message=error,
                )
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log sync: {e}")

    # ── Scheduler ─────────────────────────────────────────────────────────

    def start(self):
        """Start background data collection tasks."""
        if self.is_running:
            logger.warning("Data collector already running")
            return

        logger.info("🔄 Starting background data collector...")

        self.scheduler.add_job(
            self.collect_gold_data,
            IntervalTrigger(minutes=settings.GOLD_UPDATE_INTERVAL),
            id="collect_gold",
            name="Collect Gold Data",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.add_job(
            self.collect_stock_data,
            IntervalTrigger(minutes=settings.STOCK_UPDATE_INTERVAL),
            id="collect_stocks",
            name="Collect Stock Data",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.add_job(
            self.collect_commodity_data,
            IntervalTrigger(minutes=30),
            id="collect_commodities",
            name="Collect Commodity Data",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("✅ Background data collector started")

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        logger.info("🛑 Stopping background data collector...")
        self.scheduler.shutdown()
        self.is_running = False


# Singleton
data_collector = DataCollector()
