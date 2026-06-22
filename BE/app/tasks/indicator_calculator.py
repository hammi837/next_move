"""
Background task: calculate and store technical indicators for all tracked symbols.
Runs every hour via APScheduler.
"""

import asyncio
import logging
from functools import partial

from app.db.database import SessionLocal
from app.db.models import MarketMetadata
from app.services.technical_analysis import technical_analysis_service

logger = logging.getLogger(__name__)


async def calculate_all_indicators():
    """Calculate and store indicators for every active symbol."""
    db = SessionLocal()
    try:
        symbols = [
            row.symbol
            for row in db.query(MarketMetadata)
                         .filter(MarketMetadata.is_active == 1)
                         .all()
        ]
    finally:
        db.close()

    if not symbols:
        logger.warning("No active symbols found for indicator calculation")
        return

    logger.info(f"📊 Calculating indicators for {len(symbols)} symbols…")

    loop = asyncio.get_event_loop()

    for symbol in symbols:
        try:
            indicators = await loop.run_in_executor(
                None,
                partial(technical_analysis_service.calculate_all_indicators, symbol, 120),
            )
            if indicators:
                await loop.run_in_executor(
                    None,
                    partial(technical_analysis_service.store_indicators, symbol, indicators),
                )
                logger.info(f"✅ Indicators stored for {symbol}")
            else:
                logger.warning(f"⚠️  Not enough data for {symbol}")
        except Exception as e:
            logger.error(f"❌ Failed indicators for {symbol}: {e}")

    logger.info("✅ Indicator calculation cycle complete")
