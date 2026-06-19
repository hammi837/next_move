from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.db.database import init_db

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

app.include_router(gold_router, prefix="/api/gold", tags=["Gold"])
app.include_router(stocks_router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
