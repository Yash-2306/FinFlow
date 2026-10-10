"""Pydantic v2 schemas for FinFlow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------


class TransactionBase(BaseModel):
    """Shared transaction fields."""

    customer_id: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    merchant_category: str
    merchant_name: str
    transaction_type: Literal["purchase", "withdrawal", "transfer"]
    location_city: str
    location_country: str
    timestamp: datetime
    risk_score: float = Field(..., ge=0.0, le=1.0)
    is_anomaly: bool


class TransactionRead(TransactionBase):
    """Schema returned to API consumers (is_anomaly is exposed for dashboard)."""

    model_config = ConfigDict(from_attributes=True)

    id: str


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    total: int
    limit: int
    offset: int
    items: list[TransactionRead]


# ---------------------------------------------------------------------------
# Generation schemas
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """Request body for /api/transactions/generate."""

    count: int = Field(10, ge=1, le=500)


class GenerateResponse(BaseModel):
    """Response from /api/transactions/generate."""

    generated: int
    flagged: int
    transactions: list[TransactionRead]


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------


class CategoryStats(BaseModel):
    """Per-category breakdown stats."""

    category: str
    count: int
    total_volume: float
    avg_amount: float
    anomaly_count: int


class AggregateStats(BaseModel):
    """Overall aggregate statistics."""

    total_transactions: int
    total_flagged: int
    total_volume: float
    flag_rate_pct: float
    avg_transaction_amount: float
    category_breakdown: list[CategoryStats]


class WindowStats(BaseModel):
    """Stats for a single rolling time window."""

    window: str
    transaction_count: int
    flagged_count: int
    flag_rate_pct: float


class RollingWindowStats(BaseModel):
    """Rolling window stats across multiple windows."""

    windows: list[WindowStats]


class RiskBucket(BaseModel):
    """A single bucket in the risk-score histogram."""

    bucket: str
    count: int


class RiskDistribution(BaseModel):
    """Risk score histogram."""

    buckets: list[RiskBucket]


# ---------------------------------------------------------------------------
# Health schema
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    transaction_count: int
    model_trained: bool
