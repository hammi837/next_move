import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.db.database import init_db
from app.services.cache_service import cache_service

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database tables
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Start background data collector
    try:
        from app.tasks.data_collector import data_collector
        data_collector.start()
        logger.info("✅ Background data collector started")
        # Fire initial collection as a non-blocking background task
        # so the server finishes startup immediately
        async def _initial_collect():
            logger.info("⏳ Running initial data collection in background...")
            try:
                # Clear stale dashboard cache first
                cache_service.delete("dashboard_summary")
                await data_collector.seed_historical_data()   # seed 7-day history first
                await data_collector.collect_gold_data()
                await data_collector.collect_stock_data()
                await data_collector.collect_commodity_data()
                # Clear again so next request gets fresh data with real changes
                cache_service.delete("dashboard_summary")
                logger.info("✅ Initial data collection complete")
            except Exception as ex:
                logger.warning(f"⚠️ Initial data collection error: {ex}")

        asyncio.create_task(_initial_collect())
    except Exception as e:
        logger.warning(f"⚠️ Background data collector failed to start: {e}")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("🛑 Shutting down application...")
    try:
        from app.tasks.data_collector import data_collector
        data_collector.stop()
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time trading trend analysis and prediction platform for Gold, Stocks, and Commodities.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health & Root ────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ── Error handler ────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Register routers ────────────────────────────────────────────────────

from app.api.routes.gold import router as gold_router          # noqa: E402
from app.api.routes.stocks import router as stocks_router      # noqa: E402
from app.api.routes.dashboard import router as dashboard_router # noqa: E402
from app.api.routes.analysis import router as analysis_router   # noqa: E402
from app.api.routes.indicators import router as indicators_router # noqa: E402
from app.api.routes.predictions import router as predictions_router # noqa: E402

app.include_router(gold_router,        prefix="/api/gold",        tags=["Gold"])
app.include_router(stocks_router,      prefix="/api/stocks",      tags=["Stocks"])
app.include_router(dashboard_router,   prefix="/api/dashboard",   tags=["Dashboard"])
app.include_router(analysis_router,    prefix="/api/analysis",    tags=["Analysis"])
app.include_router(indicators_router,  prefix="/api/indicators",  tags=["Technical Indicators"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["ML Predictions"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
