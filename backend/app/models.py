"""SQLAlchemy ORM models for FinFlow."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    """Represents a single financial transaction."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    merchant_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    merchant_name: Mapped[str] = mapped_column(String(128), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    location_city: Mapped[str] = mapped_column(String(64), nullable=False)
    location_country: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, index=True
    )
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
