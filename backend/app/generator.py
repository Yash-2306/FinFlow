"""Synthetic financial transaction generator for FinFlow.

Generates realistic transactions with ~8% injected anomalies covering:
  - Extreme amounts (10× category normal)
  - Rapid velocity (same customer, 5 txns in 1 minute)
  - Geographic jumps (impossible location change)
  - Odd-hours large transactions (3-5 AM)
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

MERCHANT_CATEGORIES: list[str] = [
    "groceries",
    "electronics",
    "travel",
    "dining",
    "fuel",
    "jewelry",
    "gaming",
    "healthcare",
]

# Normal amount range (min, max) and typical distribution parameters per category
CATEGORY_AMOUNT_PARAMS: dict[str, dict[str, float]] = {
    "groceries":   {"min": 10.0,  "max": 80.0,   "mean": 45.0,  "std": 18.0},
    "electronics": {"min": 50.0,  "max": 500.0,  "mean": 200.0, "std": 100.0},
    "travel":      {"min": 100.0, "max": 2000.0, "mean": 600.0, "std": 350.0},
    "dining":      {"min": 10.0,  "max": 150.0,  "mean": 45.0,  "std": 25.0},
    "fuel":        {"min": 20.0,  "max": 120.0,  "mean": 55.0,  "std": 20.0},
    "jewelry":     {"min": 50.0,  "max": 3000.0, "mean": 500.0, "std": 400.0},
    "gaming":      {"min": 5.0,   "max": 100.0,  "mean": 30.0,  "std": 20.0},
    "healthcare":  {"min": 20.0,  "max": 800.0,  "mean": 150.0, "std": 120.0},
}

MERCHANTS_BY_CATEGORY: dict[str, list[str]] = {
    "groceries":   ["Whole Foods", "Kroger", "Trader Joe's", "Aldi", "Publix", "Safeway"],
    "electronics": ["Best Buy", "Apple Store", "Newegg", "Micro Center", "B&H Photo"],
    "travel":      ["Delta Airlines", "Marriott", "Airbnb", "Expedia", "United Airlines", "Hilton"],
    "dining":      ["McDonald's", "Cheesecake Factory", "Olive Garden", "Chipotle", "Denny's"],
    "fuel":        ["Shell", "ExxonMobil", "BP", "Chevron", "Sunoco", "Marathon"],
    "jewelry":     ["Tiffany & Co.", "Zales", "Kay Jewelers", "Pandora", "Cartier"],
    "gaming":      ["Steam", "PlayStation Store", "Xbox Game Pass", "Nintendo eShop", "Epic Games"],
    "healthcare":  ["CVS Pharmacy", "Walgreens", "LabCorp", "Quest Diagnostics", "United Health"],
}

TRANSACTION_TYPES: list[str] = ["purchase", "withdrawal", "transfer"]

CITIES_COUNTRIES: list[tuple[str, str]] = [
    ("New York", "US"),
    ("Los Angeles", "US"),
    ("Chicago", "US"),
    ("Houston", "US"),
    ("Phoenix", "US"),
    ("Philadelphia", "US"),
    ("San Antonio", "US"),
    ("San Diego", "US"),
    ("Dallas", "US"),
    ("San Jose", "US"),
    ("London", "GB"),
    ("Toronto", "CA"),
    ("Sydney", "AU"),
    ("Tokyo", "JP"),
    ("Paris", "FR"),
    ("Berlin", "DE"),
    ("Dubai", "AE"),
    ("Singapore", "SG"),
    ("Mumbai", "IN"),
    ("São Paulo", "BR"),
]

# Anomaly injection rate
ANOMALY_RATE: float = 0.08


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


def _normal_amount(category: str, rng: random.Random) -> float:
    """Return a realistic amount for the given category using a truncated normal."""
    params = CATEGORY_AMOUNT_PARAMS[category]
    raw = rng.gauss(params["mean"], params["std"])
    return round(_clamp(raw, params["min"], params["max"]), 2)


def _extreme_amount(category: str, rng: random.Random) -> float:
    """Return an extreme amount (10× the category mean)."""
    params = CATEGORY_AMOUNT_PARAMS[category]
    multiplier = rng.uniform(8.0, 12.0)
    return round(params["mean"] * multiplier, 2)


def _random_city(rng: random.Random) -> tuple[str, str]:
    return rng.choice(CITIES_COUNTRIES)


def _geo_jump_city(current: tuple[str, str], rng: random.Random) -> tuple[str, str]:
    """Return a city guaranteed to be different from the current one."""
    choices = [c for c in CITIES_COUNTRIES if c != current]
    return rng.choice(choices)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_transaction(
    *,
    rng: random.Random,
    customer_id: str | None = None,
    timestamp: datetime | None = None,
    force_anomaly: bool = False,
    anomaly_type: str | None = None,
) -> dict[str, Any]:
    """Create a single synthetic transaction dict.

    Parameters
    ----------
    rng:
        Random number generator (for reproducibility in tests).
    customer_id:
        Override the customer UUID. Generated randomly if *None*.
    timestamp:
        Transaction timestamp. Defaults to *now* (UTC).
    force_anomaly:
        If *True*, inject an anomaly regardless of the base rate.
    anomaly_type:
        One of ``"extreme_amount"``, ``"velocity"``, ``"geo_jump"``,
        ``"odd_hours"``. Randomly chosen if *force_anomaly* is *True*
        and this is *None*.
    """
    if timestamp is None:
        timestamp = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    if customer_id is None:
        customer_id = str(uuid.uuid4())

    category = rng.choice(MERCHANT_CATEGORIES)
    city, country = _random_city(rng)
    merchant = rng.choice(MERCHANTS_BY_CATEGORY[category])
    txn_type = rng.choices(
        TRANSACTION_TYPES,
        weights=[0.75, 0.15, 0.10],
        k=1,
    )[0]

    # Decide whether to inject an anomaly
    inject = force_anomaly or (rng.random() < ANOMALY_RATE)

    if inject and anomaly_type is None:
        anomaly_type = rng.choice(["extreme_amount", "velocity", "geo_jump", "odd_hours"])

    is_anomaly = inject
    amount = _normal_amount(category, rng)

    if inject:
        if anomaly_type == "extreme_amount":
            amount = _extreme_amount(category, rng)

        elif anomaly_type == "geo_jump":
            # Teleport to a distant city — the detector uses velocity / location logic
            city, country = _geo_jump_city((city, country), rng)
            amount = _extreme_amount(category, rng)

        elif anomaly_type == "odd_hours":
            # Force timestamp to 3-5 AM with a large amount
            hour = rng.randint(3, 5)
            timestamp = timestamp.replace(hour=hour, minute=rng.randint(0, 59))
            amount = _extreme_amount(category, rng)

        # "velocity" anomaly is purely a behavioral pattern — no single-txn changes needed

    return {
        "id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "amount": amount,
        "currency": "USD",
        "merchant_category": category,
        "merchant_name": merchant,
        "transaction_type": txn_type,
        "location_city": city,
        "location_country": country,
        "timestamp": timestamp,
        "is_anomaly": is_anomaly,
        "risk_score": 0.0,  # filled in by detector
    }


def generate_seed_transactions(
    n: int = 500,
    seed: int = 42,
    start_time: datetime | None = None,
) -> list[dict[str, Any]]:
    """Generate *n* historical transactions spread over the past 7 days.

    A fixed pool of 50 customer IDs is used so velocity features are
    meaningful.
    """
    rng = random.Random(seed)

    if start_time is None:
        start_time = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    # Fixed pool of customers
    customer_pool = [str(uuid.UUID(int=i)) for i in range(50)]

    # Spread timestamps across 7 days, slightly randomly
    span_seconds = 7 * 24 * 3600
    transactions: list[dict[str, Any]] = []

    for i in range(n):
        offset = (i / n) * span_seconds + rng.gauss(0, 300)
        offset = _clamp(offset, 0, span_seconds)
        ts = start_time - timedelta(seconds=span_seconds - offset)
        customer_id = rng.choice(customer_pool)
        txn = make_transaction(rng=rng, customer_id=customer_id, timestamp=ts)
        transactions.append(txn)

    return transactions


def generate_transactions(
    n: int = 10,
    seed: int | None = None,
    existing_transactions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate *n* new real-time transactions.

    For velocity anomalies, we occasionally reuse a customer_id from
    *existing_transactions* and generate rapid bursts.
    """
    rng = random.Random(seed)
    existing = existing_transactions or []

    # Build a small pool of recent customer IDs for velocity injection
    recent_customers: list[str] = []
    if existing:
        recent_customers = [t["customer_id"] for t in existing[-100:]]

    results: list[dict[str, Any]] = []
    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    i = 0
    while i < n:
        inject = rng.random() < ANOMALY_RATE
        if inject and recent_customers and rng.random() < 0.3:
            # Velocity anomaly: same customer, rapid burst of up to 5 txns
            cid = rng.choice(recent_customers)
            burst = min(rng.randint(4, 6), n - i)
            for b in range(burst):
                ts = now - timedelta(seconds=rng.randint(0, 30))
                txn = make_transaction(
                    rng=rng,
                    customer_id=cid,
                    timestamp=ts,
                    force_anomaly=(b == 0),
                    anomaly_type="velocity",
                )
                results.append(txn)
            i += burst
        else:
            txn = make_transaction(rng=rng, timestamp=now)
            results.append(txn)
            i += 1

    return results
