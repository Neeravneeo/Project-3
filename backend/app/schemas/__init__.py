"""
Pydantic v2 schemas — public API surface.
All response/request models live in their own modules.
"""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.hedge import HedgeEventResponse, HedgeStatusResponse
from app.schemas.market_data import OHLCVBar, QuoteResponse, TickerSearchResult
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.portfolio import PortfolioResponse, PortfolioSummary
from app.schemas.position import PositionResponse
from app.schemas.risk import RiskMetricsResponse
from app.schemas.signal import AggregatedSignalResponse, SignalResponse, StrategyContribution
from app.schemas.strategy import StrategyResponse, StrategyUpdate
from app.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Portfolio
    "PortfolioResponse",
    "PortfolioSummary",
    "PositionResponse",
    # Orders
    "OrderCreate",
    "OrderResponse",
    # Strategies
    "StrategyResponse",
    "StrategyUpdate",
    # Signals
    "SignalResponse",
    "AggregatedSignalResponse",
    "StrategyContribution",
    # Risk
    "RiskMetricsResponse",
    # Hedge
    "HedgeStatusResponse",
    "HedgeEventResponse",
    # Market data
    "QuoteResponse",
    "OHLCVBar",
    "TickerSearchResult",
    # Common
    "PaginatedResponse",
    "ErrorResponse",
]
