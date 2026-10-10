"""FinFlow FastAPI application entry point.

Startup sequence:
  1. Configure structlog
  2. Initialise the SQLite database (create tables)
  3. Seed 500 historical transactions
  4. Train the Isolation Forest anomaly detector
  5. Mount routers and middleware
"""

from __future__ import annotations

import re
import traceback
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import close_db, init_db
from app.detector import apply_detection, detector
from app.generator import generate_seed_transactions
from app.routers import analytics as analytics_router
from app.routers import health as health_router
from app.routers import transactions as transactions_router

# ---------------------------------------------------------------------------
# Structlog configuration
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(__import__("logging"), settings.LOG_LEVEL.upper(), 20)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# In-memory transaction store (list of dicts)
# ---------------------------------------------------------------------------

transaction_store: list[dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    log.info("startup.begin", environment=settings.ENVIRONMENT)

    # 1. Init database
    await init_db()

    # 2. Seed 500 historical transactions
    log.info("startup.seeding_transactions")
    seed_txns = generate_seed_transactions(n=500, seed=42)

    # 3. Train the detector on the raw seed data first (before scoring)
    log.info("startup.training_detector")
    detector.train(seed_txns)

    # 4. Score each seed transaction
    for txn in seed_txns:
        apply_detection(txn, seed_txns)

    transaction_store.extend(seed_txns)
    flagged = sum(1 for t in transaction_store if t.get("is_anomaly"))
    log.info(
        "startup.complete",
        total_seeded=len(transaction_store),
        flagged=flagged,
    )

    yield

    # Shutdown
    log.info("shutdown.begin")
    await close_db()
    log.info("shutdown.complete")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FinFlow",
    description="Real-Time Financial Transaction Anomaly Detection Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

_HARDCODED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
]

# Vercel preview URLs — handled via regex in allow_origin_regex
_VERCEL_REGEX = r"https://.*\.vercel\.app"


def _build_cors_origins() -> list[str]:
    origins = list(_HARDCODED_ORIGINS)
    origins.extend(settings.extra_cors_origins)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_origin_regex=_VERCEL_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Rate limiting
# ------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------------------------------------------
# Global exception handler
# ------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler that returns structured JSON errors."""
    log.error(
        "unhandled_exception",
        path=str(request.url),
        error=str(exc),
        trace=traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)},
    )


# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(health_router.router)
app.include_router(transactions_router.router)
app.include_router(analytics_router.router)


# ------------------------------------------------------------------
# Root
# ------------------------------------------------------------------


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """API root — returns a welcome message."""
    return {
        "message": "FinFlow Anomaly Detection API",
        "docs": "/docs",
        "health": "/api/health",
    }
