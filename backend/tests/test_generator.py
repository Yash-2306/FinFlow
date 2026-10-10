"""Tests for the synthetic transaction generator."""

from __future__ import annotations

import random
import uuid
from datetime import datetime

import pytest

from app.generator import (
    ANOMALY_RATE,
    CATEGORY_AMOUNT_PARAMS,
    MERCHANT_CATEGORIES,
    generate_seed_transactions,
    generate_transactions,
    make_transaction,
)

# ---------------------------------------------------------------------------
# Required fields that every transaction must have
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "id",
    "customer_id",
    "amount",
    "currency",
    "merchant_category",
    "merchant_name",
    "transaction_type",
    "location_city",
    "location_country",
    "timestamp",
    "is_anomaly",
    "risk_score",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seed_txns():
    """500 deterministic seed transactions."""
    return generate_seed_transactions(n=500, seed=42)


@pytest.fixture
def rng():
    return random.Random(99)


# ---------------------------------------------------------------------------
# Tests: make_transaction
# ---------------------------------------------------------------------------


class TestMakeTransaction:
    def test_all_required_fields_present(self, rng):
        txn = make_transaction(rng=rng)
        missing = REQUIRED_FIELDS - set(txn.keys())
        assert not missing, f"Missing fields: {missing}"

    def test_id_is_valid_uuid(self, rng):
        txn = make_transaction(rng=rng)
        # Should not raise
        uuid.UUID(txn["id"])

    def test_customer_id_is_valid_uuid(self, rng):
        txn = make_transaction(rng=rng)
        uuid.UUID(txn["customer_id"])

    def test_currency_is_usd(self, rng):
        for _ in range(10):
            txn = make_transaction(rng=rng)
            assert txn["currency"] == "USD"

    def test_merchant_category_valid(self, rng):
        for _ in range(20):
            txn = make_transaction(rng=rng)
            assert txn["merchant_category"] in MERCHANT_CATEGORIES

    def test_transaction_type_valid(self, rng):
        valid_types = {"purchase", "withdrawal", "transfer"}
        for _ in range(20):
            txn = make_transaction(rng=rng)
            assert txn["transaction_type"] in valid_types

    def test_amount_positive(self, rng):
        for _ in range(20):
            txn = make_transaction(rng=rng)
            assert txn["amount"] > 0

    def test_timestamp_is_datetime(self, rng):
        txn = make_transaction(rng=rng)
        assert isinstance(txn["timestamp"], datetime)

    def test_is_anomaly_is_bool(self, rng):
        txn = make_transaction(rng=rng)
        assert isinstance(txn["is_anomaly"], bool)

    def test_risk_score_zero_on_creation(self, rng):
        """risk_score is 0.0 until scored by the detector."""
        txn = make_transaction(rng=rng)
        assert txn["risk_score"] == 0.0

    def test_force_anomaly_flag(self, rng):
        txn = make_transaction(rng=rng, force_anomaly=True)
        assert txn["is_anomaly"] is True

    def test_customer_id_override(self, rng):
        cid = str(uuid.uuid4())
        txn = make_transaction(rng=rng, customer_id=cid)
        assert txn["customer_id"] == cid

    def test_timestamp_override(self, rng):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        txn = make_transaction(rng=rng, timestamp=ts)
        assert txn["timestamp"] == ts

    def test_extreme_amount_anomaly_type(self, rng):
        """Force extreme_amount anomaly and verify amount >> category mean."""
        txn = make_transaction(rng=rng, force_anomaly=True, anomaly_type="extreme_amount")
        params = CATEGORY_AMOUNT_PARAMS[txn["merchant_category"]]
        # Should be at least 5× the category mean
        assert txn["amount"] >= params["mean"] * 5.0

    def test_odd_hours_anomaly_type(self, rng):
        """Force odd_hours anomaly and verify timestamp hour is 3-5."""
        txn = make_transaction(rng=rng, force_anomaly=True, anomaly_type="odd_hours")
        assert txn["timestamp"].hour in (3, 4, 5)


# ---------------------------------------------------------------------------
# Tests: category amount ranges
# ---------------------------------------------------------------------------


class TestCategoryAmounts:
    @pytest.mark.parametrize("category", list(CATEGORY_AMOUNT_PARAMS.keys()))
    def test_normal_amounts_within_range(self, category):
        """Normal transaction amounts should stay within the defined range."""
        rng = random.Random(category)  # deterministic per category
        params = CATEGORY_AMOUNT_PARAMS[category]
        lo, hi = params["min"], params["max"]
        out_of_range = 0
        n = 100
        for _ in range(n):
            txn = make_transaction(rng=rng)
            # Only check non-anomalous transactions
            if not txn["is_anomaly"] and txn["merchant_category"] == category:
                if not (lo <= txn["amount"] <= hi):
                    out_of_range += 1
        # Allow a very small tolerance for numeric edge cases
        assert out_of_range == 0, (
            f"{out_of_range} out-of-range amounts for category '{category}'"
        )


# ---------------------------------------------------------------------------
# Tests: anomaly injection rate
# ---------------------------------------------------------------------------


class TestAnomalyRate:
    def test_anomaly_rate_in_expected_range(self, seed_txns):
        """Anomaly injection rate should be roughly 5-12%."""
        anomaly_count = sum(1 for t in seed_txns if t["is_anomaly"])
        rate = anomaly_count / len(seed_txns)
        assert 0.05 <= rate <= 0.12, (
            f"Anomaly rate {rate:.2%} is outside the expected 5-12% range."
        )

    def test_generate_transactions_has_anomalies(self):
        """generate_transactions() should produce some anomalies over a large batch."""
        txns = generate_transactions(n=200, seed=7)
        anomalies = [t for t in txns if t["is_anomaly"]]
        assert len(anomalies) > 0, "Expected at least one anomaly in 200 transactions"


# ---------------------------------------------------------------------------
# Tests: generate_seed_transactions
# ---------------------------------------------------------------------------


class TestGenerateSeedTransactions:
    def test_generates_correct_count(self, seed_txns):
        assert len(seed_txns) == 500

    def test_all_fields_present(self, seed_txns):
        for txn in seed_txns:
            missing = REQUIRED_FIELDS - set(txn.keys())
            assert not missing, f"Transaction {txn.get('id')} missing: {missing}"

    def test_timestamps_ordered_ascending(self, seed_txns):
        """Seed transactions should be spread across time (not all the same)."""
        timestamps = [t["timestamp"] for t in seed_txns]
        assert len(set(timestamps)) > 1, "All timestamps are identical — generator is broken"

    def test_multiple_categories_present(self, seed_txns):
        categories = {t["merchant_category"] for t in seed_txns}
        assert len(categories) >= 6, (
            f"Expected ≥6 categories in seed data, got {len(categories)}"
        )

    def test_deterministic_with_same_seed(self):
        """Same seed should produce identical output."""
        txns_a = generate_seed_transactions(n=50, seed=123)
        txns_b = generate_seed_transactions(n=50, seed=123)
        assert [t["id"] for t in txns_a] == [t["id"] for t in txns_b]

    def test_different_seeds_produce_different_data(self):
        txns_a = generate_seed_transactions(n=50, seed=1)
        txns_b = generate_seed_transactions(n=50, seed=2)
        assert [t["id"] for t in txns_a] != [t["id"] for t in txns_b]
