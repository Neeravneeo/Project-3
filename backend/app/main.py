"""
AI Trading & Auto-Hedging Intelligence Platform
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import create_db_pool, close_db_pool
from app.core.logging import setup_logging
from app.api.v1 import auth, portfolio, strategies, signals, orders, risk, hedge, market_data, ai_insights
from app.api.v1.websocket import router as ws_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize and teardown resources."""
    # Startup
    app.state.db_pool = await create_db_pool()
    app.state.redis = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    yield
    # Shutdown
    await close_db_pool(app.state.db_pool)
    await app.state.redis.aclose()


app = FastAPI(
    title="AI Trading & Auto-Hedging Platform",
    description="AI-powered trading with integrated auto-hedging engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ─── API Routers ─────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router,         prefix=f"{PREFIX}/auth",        tags=["Authentication"])
app.include_router(portfolio.router,    prefix=f"{PREFIX}/portfolio",   tags=["Portfolio"])
app.include_router(strategies.router,   prefix=f"{PREFIX}/strategies",  tags=["Strategies"])
app.include_router(signals.router,      prefix=f"{PREFIX}/signals",     tags=["Signals"])
app.include_router(orders.router,       prefix=f"{PREFIX}/orders",      tags=["Orders"])
app.include_router(risk.router,         prefix=f"{PREFIX}/risk",        tags=["Risk"])
app.include_router(hedge.router,        prefix=f"{PREFIX}/hedge",       tags=["Hedging"])
app.include_router(market_data.router,  prefix=f"{PREFIX}/market",      tags=["Market Data"])
app.include_router(ai_insights.router,  prefix=f"{PREFIX}/insights",    tags=["AI Insights"])
app.include_router(ws_router,           prefix="/ws",                   tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "version": "1.0.0", "environment": settings.app_env}
