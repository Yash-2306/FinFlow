"""Tests for the anomaly detection engine.

All tests use deterministic seed data — no randomness.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import pytest

from app.detector import AnomalyDetector, ANOMALY_THRESHOLD
from app.generator import (
    CATEGORY_AMOUNT_PARAMS,
    make_transaction,
    generate_seed_transactions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seed_transactions():
    """500 deterministic seed transactions."""
    return generate_seed_transactions(n=500, seed=42)


@pytest.fixture(scope="module")
def trained_detector(seed_transactions):
    """A detector trained on the seed transactions."""
    det = AnomalyDetector()
    det.train(seed_transactions)
    return det


@pytest.fixture
def rng():
    """Fixed-seed RNG for deterministic test helpers."""
    return random.Random(0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_normal(category: str, rng: random.Random) -> dict:
    """Create a normal (non-anomalous) transaction for *category*."""
    params = CATEGORY_AMOUNT_PARAMS[category]
    amount = params["mean"]  # exactly the mean → z-score = 0
    txn = make_transaction(rng=rng)
    txn["merchant_category"] = category
    txn["amount"] = amount
    txn["is_anomaly"] = False
    txn["timestamp"] = datetime(2024, 6, 15, 14, 0, 0)  # ordinary afternoon
    return txn


def _make_extreme_amount(category: str, rng: random.Random) -> dict:
    """Create a transaction with an extreme (10× mean) amount."""
    params = CATEGORY_AMOUNT_PARAMS[category]
    txn = make_transaction(rng=rng)
    txn["merchant_category"] = category
    txn["amount"] = params["mean"] * 11.0  # well above 10×
    txn["is_anomaly"] = True
    txn["timestamp"] = datetime(2024, 6, 15, 14, 0, 0)
    return txn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDetectorTraining:
    def test_detector_is_trained_after_fit(self, trained_detector):
        """Detector reports trained after calling train()."""
        assert trained_detector.is_trained() is True

    def test_detector_untrained_by_default(self):
        """A fresh detector reports not trained."""
        det = AnomalyDetector()
        assert det.is_trained() is False


class TestNormalTransactions:
    """Normal transactions should score below the anomaly threshold."""

    @pytest.mark.parametrize("category", list(CATEGORY_AMOUNT_PARAMS.keys()))
    def test_normal_scores_below_threshold(
        self, category, trained_detector, seed_transactions, rng
    ):
        txn = _make_normal(category, rng)
        score = trained_detector.score(txn, seed_transactions)
        assert score < ANOMALY_THRESHOLD, (
            f"Expected normal {category} txn to score < {ANOMALY_THRESHOLD}, got {score}"
        )


class TestExtremeAmountAnomalies:
    """Extreme-amount transactions should be flagged."""

    @pytest.mark.parametrize("category", ["groceries", "dining", "gaming", "fuel"])
    def test_extreme_amount_flagged(
        self, category, trained_detector, seed_transactions, rng
    ):
        txn = _make_extreme_amount(category, rng)
        score = trained_detector.score(txn, seed_transactions)
        assert score > ANOMALY_THRESHOLD, (
            f"Expected extreme {category} txn to score > {ANOMALY_THRESHOLD}, got {score}"
        )


class TestVelocityAnomalies:
    """High velocity (>4 txns in 60 s) should push scores up."""

    def test_velocity_increases_score(self, trained_detector, seed_transactions, rng):
        now = datetime.utcnow()
        customer_id = "velocity-test-customer"

        # Build a burst: 5 transactions in 30 seconds
        burst: list[dict] = []
        for i in range(5):
            ts = now - timedelta(seconds=30 - i * 5)
            txn = make_transaction(rng=rng, customer_id=customer_id, timestamp=ts)
            txn["amount"] = CATEGORY_AMOUNT_PARAMS[txn["merchant_category"]]["mean"]
            burst.append(txn)

        context = seed_transactions + burst[:-1]
        candidate = burst[-1]
        score = trained_detector.score(candidate, context)

        # Velocity component alone should push score meaningfully higher than 0
        assert score > 0.15, f"Velocity signal should raise score, got {score}"

    def test_high_velocity_flagged(self, trained_detector, seed_transactions, rng):
        now = datetime.utcnow()
        customer_id = "high-velocity-customer"

        # 6 rapid transactions within 10 seconds
        burst: list[dict] = []
        for i in range(6):
            ts = now - timedelta(seconds=10 - i)
            txn = make_transaction(rng=rng, customer_id=customer_id, timestamp=ts)
            txn["amount"] = CATEGORY_AMOUNT_PARAMS[txn["merchant_category"]]["mean"]
            burst.append(txn)

        context = seed_transactions + burst[:-1]
        candidate = burst[-1]
        score = trained_detector.score(candidate, context)
        assert score > ANOMALY_THRESHOLD, (
            f"High-velocity txn should be flagged, got {score}"
        )


class TestRiskScoreBounds:
    """risk_score must always be in [0, 1]."""

    def test_score_in_bounds_for_normal(
        self, trained_detector, seed_transactions, rng
    ):
        txn = _make_normal("groceries", rng)
        score = trained_detector.score(txn, seed_transactions)
        assert 0.0 <= score <= 1.0

    def test_score_in_bounds_for_extreme(
        self, trained_detector, seed_transactions, rng
    ):
        txn = _make_extreme_amount("electronics", rng)
        score = trained_detector.score(txn, seed_transactions)
        assert 0.0 <= score <= 1.0

    def test_score_in_bounds_for_all_seeds(self, trained_detector, seed_transactions):
        for txn in seed_transactions:
            score = trained_detector.score(txn, seed_transactions)
            assert 0.0 <= score <= 1.0, f"Score out of bounds: {score} for txn {txn['id']}"


class TestZScoreSignal:
    """Verify Z-score component behaves as expected."""

    def test_zscore_high_for_extreme_amount(self, trained_detector, rng):
        # Force a grossly inflated amount
        txn = make_transaction(rng=rng)
        txn["merchant_category"] = "groceries"
        txn["amount"] = 10_000.0  # absurdly large for groceries
        z_signal = trained_detector._zscore_signal(txn)
        assert z_signal == 1.0  # capped at 1.0

    def test_zscore_low_for_mean_amount(self, trained_detector, rng):
        txn = make_transaction(rng=rng)
        txn["merchant_category"] = "dining"
        txn["amount"] = CATEGORY_AMOUNT_PARAMS["dining"]["mean"]
        z_signal = trained_detector._zscore_signal(txn)
        assert z_signal == 0.0
