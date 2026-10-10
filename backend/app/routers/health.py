"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter

from app.detector import detector
from app.schemas import HealthResponse
from app.config import settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status."""
    from app.main import transaction_store  # imported here to avoid circular import

    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        transaction_count=len(transaction_store),
        model_trained=detector.is_trained(),
    )
