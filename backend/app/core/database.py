"""Async database connection pool using asyncpg + SQLAlchemy 2.0."""

from typing import Any
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ─── SQLAlchemy Async Engine ──────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── asyncpg Raw Pool (for high-performance queries) ─────────────────────────
async def create_db_pool() -> asyncpg.Pool:
    """Create a raw asyncpg connection pool for the app lifespan."""
    # Build DSN from asyncpg-compatible URL (no +asyncpg driver prefix)
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=5,
        max_size=20,
        command_timeout=60,
    )
    return pool


async def close_db_pool(pool: asyncpg.Pool) -> None:
    """Close the asyncpg connection pool."""
    await pool.close()
