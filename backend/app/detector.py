"""Anomaly detection engine for FinFlow.

Combines three signals:
1. Isolation Forest (trained on seed transactions)
2. Z-score vs category mean/std
3. Velocity (transaction count in last 60 s for same customer)

Final risk_score = weighted average of the three normalised signals.
Transactions with risk_score > 0.65 are flagged as anomalies.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANOMALY_THRESHOLD: float = 0.65
VELOCITY_WINDOW_SECONDS: int = 60
VELOCITY_MAX_THRESHOLD: int = 4  # > 4 txns in 60 s → flagged

# Weights for the three signals (must sum to 1.0)
WEIGHT_IF: float = 0.40
WEIGHT_ZSCORE: float = 0.35
WEIGHT_VELOCITY: float = 0.25


# ---------------------------------------------------------------------------
# Detector state (module-level singleton — replaced at startup)
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Stateful anomaly detector that wraps Isolation Forest + heuristics."""

    def __init__(self) -> None:
        self._model: IsolationForest | None = None
        self._category_stats: dict[str, dict[str, float]] = {}
        self._trained: bool = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, transactions: list[dict[str, Any]]) -> None:
        """Fit the Isolation Forest on *transactions* and compute category stats.

        Parameters
        ----------
        transactions:
            List of transaction dicts as produced by :mod:`app.generator`.
        """
        if not transactions:
            return

        # Compute per-category mean / std for Z-score later
        cat_amounts: dict[str, list[float]] = defaultdict(list)
        for txn in transactions:
            cat_amounts[txn["merchant_category"]].append(txn["amount"])

        self._category_stats = {}
        for cat, amounts in cat_amounts.items():
            arr = np.array(amounts, dtype=float)
            self._category_stats[cat] = {
                "mean": float(arr.mean()),
                "std": float(arr.std()) if arr.std() > 0 else 1.0,
            }

        # Build feature matrix for Isolation Forest
        X = self._build_features(transactions, existing=transactions)

        self._model = IsolationForest(
            n_estimators=150,
            contamination=0.08,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X)
        self._trained = True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(
        self,
        transaction: dict[str, Any],
        all_transactions: list[dict[str, Any]],
    ) -> float:
        """Return a risk score in [0, 1] for *transaction*.

        Parameters
        ----------
        transaction:
            The candidate transaction dict (with at least ``amount``,
            ``merchant_category``, ``customer_id``, ``timestamp``).
        all_transactions:
            Historical transactions used to compute velocity and to provide
            context for the Isolation Forest feature vector.
        """
        if_score = self._isolation_forest_score(transaction, all_transactions)
        z_score = self._zscore_signal(transaction)
        vel_score = self._velocity_signal(transaction, all_transactions)

        risk = (
            WEIGHT_IF * if_score
            + WEIGHT_ZSCORE * z_score
            + WEIGHT_VELOCITY * vel_score
        )
        return round(float(np.clip(risk, 0.0, 1.0)), 4)

    def score_batch(
        self,
        transactions: list[dict[str, Any]],
        all_transactions: list[dict[str, Any]],
    ) -> list[float]:
        """Score a batch of transactions efficiently."""
        return [self.score(t, all_transactions) for t in transactions]

    def is_trained(self) -> bool:
        """Return *True* if the model has been trained."""
        return self._trained

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _isolation_forest_score(
        self,
        transaction: dict[str, Any],
        all_transactions: list[dict[str, Any]],
    ) -> float:
        """Map Isolation Forest decision function to [0, 1].

        Sklearn's ``decision_function`` returns negative scores for anomalies.
        We map the typical range [-0.5, 0.5] → [1, 0].
        """
        if not self._trained or self._model is None:
            return 0.0

        X = self._build_features([transaction], existing=all_transactions)
        raw: float = self._model.decision_function(X)[0]
        # Larger (more positive) raw score → more normal → lower risk
        # Typical range: [-0.5, 0.5]; clip then invert
        normalised = float(np.clip(-raw + 0.5, 0.0, 1.0))
        return normalised

    def _zscore_signal(self, transaction: dict[str, Any]) -> float:
        """Return a [0, 1] signal based on Z-score vs category mean."""
        cat = transaction.get("merchant_category", "")
        amount = float(transaction.get("amount", 0.0))
        stats = self._category_stats.get(cat, {})
        if not stats:
            return 0.0

        z = abs(amount - stats["mean"]) / stats["std"]
        # z ≥ 3 → flag (score 1.0), z = 0 → 0.0; linear scaling capped at 3
        return float(np.clip(z / 3.0, 0.0, 1.0))

    def _velocity_signal(
        self,
        transaction: dict[str, Any],
        all_transactions: list[dict[str, Any]],
    ) -> float:
        """Return a [0, 1] signal based on recent transaction velocity."""
        customer_id = transaction.get("customer_id", "")
        ts: datetime = transaction.get("timestamp", datetime.utcnow())
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)

        window_start = ts - timedelta(seconds=VELOCITY_WINDOW_SECONDS)
        count = sum(
            1
            for t in all_transactions
            if t.get("customer_id") == customer_id
            and _parse_ts(t.get("timestamp")) >= window_start
            and _parse_ts(t.get("timestamp")) <= ts
        )

        # > VELOCITY_MAX_THRESHOLD → full score; scale linearly below
        return float(np.clip(count / (VELOCITY_MAX_THRESHOLD + 1), 0.0, 1.0))

    def _build_features(
        self,
        transactions: list[dict[str, Any]],
        existing: list[dict[str, Any]],
    ) -> np.ndarray:
        """Build numeric feature matrix for Isolation Forest.

        Features per transaction:
          0. amount (log-scaled)
          1. hour_of_day
          2. day_of_week
          3. transactions_in_last_hour (velocity)
          4. amount_zscore_vs_category
        """
        rows: list[list[float]] = []
        for txn in transactions:
            ts = _parse_ts(txn.get("timestamp"))
            amount = float(txn.get("amount", 0.0))
            cat = txn.get("merchant_category", "")
            customer_id = txn.get("customer_id", "")

            # Log-scale amount
            log_amount = math.log1p(amount)

            # Time features
            hour = float(ts.hour)
            dow = float(ts.weekday())

            # Velocity in last 60 minutes (training: use existing as context)
            window_start = ts - timedelta(hours=1)
            velocity = sum(
                1
                for t in existing
                if t.get("customer_id") == customer_id
                and _parse_ts(t.get("timestamp", ts)) >= window_start
                and _parse_ts(t.get("timestamp", ts)) <= ts
            )

            # Z-score
            stats = self._category_stats.get(cat, {"mean": amount, "std": 1.0})
            z = (amount - stats["mean"]) / stats["std"]

            rows.append([log_amount, hour, dow, float(velocity), z])

        return np.array(rows, dtype=float)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(value: Any) -> datetime:
    """Parse a timestamp value to a naive :class:`datetime`."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        return datetime.fromisoformat(value).replace(tzinfo=None)
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

detector = AnomalyDetector()


def apply_detection(
    transaction: dict[str, Any],
    all_transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score *transaction* with the global detector and update in place.

    Sets ``risk_score`` and ``is_anomaly`` on *transaction* (mutates).
    Returns the same dict.
    """
    score = detector.score(transaction, all_transactions)
    transaction["risk_score"] = score
    transaction["is_anomaly"] = score > ANOMALY_THRESHOLD
    return transaction
