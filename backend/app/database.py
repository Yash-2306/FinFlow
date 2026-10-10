"""Async SQLAlchemy database setup with aiosqlite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

log = structlog.get_logger(__name__)

# Ensure the data directory exists when using SQLite
_db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
if _db_path.startswith("./"):
    _dir = os.path.dirname(_db_path)
    os.makedirs(_dir, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def init_db() -> None:
    """Create all tables defined in the ORM models."""
    from app import models  # noqa: F401 – import to register metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database.initialized")


async def close_db() -> None:
    """Dispose of the engine connection pool."""
    await engine.dispose()
    log.info("database.closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
