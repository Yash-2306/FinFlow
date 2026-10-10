"""Analytics router for FinFlow."""

from __future__ import annotations

from fastapi import APIRouter

from app import analytics
from app.schemas import (
    AggregateStats,
    RiskDistribution,
    RollingWindowStats,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats", response_model=AggregateStats)
async def get_stats() -> AggregateStats:
    """Return aggregate statistics across all transactions."""
    from app.main import transaction_store

    return analytics.compute_stats(transaction_store)


@router.get("/rolling", response_model=RollingWindowStats)
async def get_rolling_stats() -> RollingWindowStats:
    """Return rolling window statistics (60s, 5min, 1hr)."""
    from app.main import transaction_store

    return analytics.rolling_window_stats(transaction_store)


@router.get("/categories")
async def get_categories() -> list:
    """Return per-category breakdown statistics."""
    from app.main import transaction_store

    return analytics.category_breakdown(transaction_store)


@router.get("/risk-distribution", response_model=RiskDistribution)
async def get_risk_distribution() -> RiskDistribution:
    """Return the risk score histogram."""
    from app.main import transaction_store

    return analytics.risk_distribution(transaction_store)
