"""Aggregate analytics and rolling-window calculations for FinFlow."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.schemas import (
    AggregateStats,
    CategoryStats,
    RiskBucket,
    RiskDistribution,
    RollingWindowStats,
    WindowStats,
)


def compute_stats(transactions: list[dict[str, Any]]) -> AggregateStats:
    """Compute overall aggregate statistics from *transactions*.

    Parameters
    ----------
    transactions:
        List of transaction dicts (as stored in memory / returned by DB).
    """
    total = len(transactions)
    flagged = sum(1 for t in transactions if t.get("is_anomaly"))
    volume = sum(float(t.get("amount", 0.0)) for t in transactions)
    flag_rate = (flagged / total * 100.0) if total else 0.0
    avg_amount = (volume / total) if total else 0.0

    # Per-category buckets
    cat_data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "volume": 0.0, "anomaly_count": 0}
    )
    for t in transactions:
        cat = t.get("merchant_category", "unknown")
        cat_data[cat]["count"] += 1
        cat_data[cat]["volume"] += float(t.get("amount", 0.0))
        if t.get("is_anomaly"):
            cat_data[cat]["anomaly_count"] += 1

    category_breakdown = [
        CategoryStats(
            category=cat,
            count=data["count"],
            total_volume=round(data["volume"], 2),
            avg_amount=round(data["volume"] / data["count"], 2) if data["count"] else 0.0,
            anomaly_count=data["anomaly_count"],
        )
        for cat, data in sorted(cat_data.items())
    ]

    return AggregateStats(
        total_transactions=total,
        total_flagged=flagged,
        total_volume=round(volume, 2),
        flag_rate_pct=round(flag_rate, 2),
        avg_transaction_amount=round(avg_amount, 2),
        category_breakdown=category_breakdown,
    )


def rolling_window_stats(transactions: list[dict[str, Any]]) -> RollingWindowStats:
    """Compute transaction counts and flag rates for three time windows.

    Windows:
      - last 60 seconds
      - last 5 minutes
      - last 1 hour
    """
    now = datetime.utcnow()
    windows: list[tuple[str, timedelta]] = [
        ("60s", timedelta(seconds=60)),
        ("5min", timedelta(minutes=5)),
        ("1hr", timedelta(hours=1)),
    ]

    result: list[WindowStats] = []
    for label, delta in windows:
        cutoff = now - delta
        subset = [
            t for t in transactions
            if _parse_ts(t.get("timestamp", now)) >= cutoff
        ]
        count = len(subset)
        flagged = sum(1 for t in subset if t.get("is_anomaly"))
        rate = (flagged / count * 100.0) if count else 0.0
        result.append(
            WindowStats(
                window=label,
                transaction_count=count,
                flagged_count=flagged,
                flag_rate_pct=round(rate, 2),
            )
        )

    return RollingWindowStats(windows=result)


def category_breakdown(transactions: list[dict[str, Any]]) -> list[CategoryStats]:
    """Return per-category stats (delegates to :func:`compute_stats`)."""
    return compute_stats(transactions).category_breakdown


def risk_distribution(transactions: list[dict[str, Any]]) -> RiskDistribution:
    """Build a histogram of risk scores in five equal buckets."""
    buckets_def: list[tuple[str, float, float]] = [
        ("0.0-0.2", 0.0, 0.2),
        ("0.2-0.4", 0.2, 0.4),
        ("0.4-0.6", 0.4, 0.6),
        ("0.6-0.8", 0.6, 0.8),
        ("0.8-1.0", 0.8, 1.001),  # 1.001 so 1.0 falls into last bucket
    ]

    counts: dict[str, int] = {label: 0 for label, _, _ in buckets_def}
    for t in transactions:
        score = float(t.get("risk_score", 0.0))
        for label, lo, hi in buckets_def:
            if lo <= score < hi:
                counts[label] += 1
                break

    return RiskDistribution(
        buckets=[RiskBucket(bucket=label, count=counts[label]) for label, _, _ in buckets_def]
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(value: Any) -> datetime:
    """Coerce *value* to a naive :class:`datetime`."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).replace(tzinfo=None)
        except ValueError:
            return datetime.utcnow()
    return datetime.utcnow()
