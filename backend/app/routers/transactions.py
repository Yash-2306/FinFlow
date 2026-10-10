"""Transactions router for FinFlow.

Provides:
  GET  /api/transactions          — paginated list
  GET  /api/transactions/stream   — SSE stream of live transactions
  POST /api/transactions/generate — generate N new transactions
  GET  /api/transactions/{id}     — single transaction detail
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Annotated, AsyncGenerator

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.detector import apply_detection
from app.generator import generate_transactions
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
    TransactionListResponse,
    TransactionRead,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dict_to_read(txn: dict) -> TransactionRead:
    """Convert a transaction dict to a :class:`TransactionRead` schema."""
    return TransactionRead(**txn)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    flagged_only: Annotated[bool, Query()] = False,
) -> TransactionListResponse:
    """Return a paginated list of transactions.

    Parameters
    ----------
    limit:
        Maximum number of transactions to return (1–500).
    offset:
        Number of transactions to skip.
    flagged_only:
        If *true*, return only anomalous transactions.
    """
    from app.main import transaction_store

    source = list(reversed(transaction_store))  # newest first
    if flagged_only:
        source = [t for t in source if t.get("is_anomaly")]

    total = len(source)
    page = source[offset : offset + limit]

    return TransactionListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_dict_to_read(t) for t in page],
    )


@router.get("/stream")
async def stream_transactions() -> StreamingResponse:
    """SSE endpoint that streams 1-3 new transactions every 3 seconds."""

    async def _event_generator() -> AsyncGenerator[str, None]:
        from app.main import transaction_store

        while True:
            count = random.randint(1, 3)
            seed = random.randint(0, 2**31)
            new_txns = generate_transactions(
                n=count,
                seed=seed,
                existing_transactions=transaction_store[-200:],
            )
            for txn in new_txns:
                apply_detection(txn, transaction_store)
                transaction_store.append(txn)
                payload = json.dumps(txn, default=str)
                yield f"data: {payload}\n\n"
                log.debug("sse.transaction_sent", id=txn["id"], risk=txn["risk_score"])

            await asyncio.sleep(3)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_new_transactions(body: GenerateRequest) -> GenerateResponse:
    """Generate *N* new synthetic transactions, score them, and persist them.

    Parameters
    ----------
    body.count:
        Number of transactions to generate (1–500).
    """
    from app.main import transaction_store

    seed = random.randint(0, 2**31)
    new_txns = generate_transactions(
        n=body.count,
        seed=seed,
        existing_transactions=transaction_store[-500:],
    )

    for txn in new_txns:
        apply_detection(txn, transaction_store)
        transaction_store.append(txn)

    flagged = sum(1 for t in new_txns if t.get("is_anomaly"))
    log.info("transactions.generated", count=len(new_txns), flagged=flagged)

    return GenerateResponse(
        generated=len(new_txns),
        flagged=flagged,
        transactions=[_dict_to_read(t) for t in new_txns],
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(transaction_id: str) -> TransactionRead:
    """Return a single transaction by its UUID.

    Parameters
    ----------
    transaction_id:
        The UUID of the transaction to retrieve.
    """
    from app.main import transaction_store

    for txn in transaction_store:
        if txn.get("id") == transaction_id:
            return _dict_to_read(txn)

    raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
