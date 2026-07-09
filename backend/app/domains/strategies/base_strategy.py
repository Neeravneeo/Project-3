"""
Abstract BaseStrategy — all trading strategies inherit from this.

Every strategy must:
1. Accept a DataFrame of OHLCV data
2. Return a SignalResult with direction, confidence, indicators snapshot
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pandas as pd


class SignalDirection(str, Enum):
    BUY  = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class SignalResult:
    """Output of a strategy's generate_signal() call."""
    symbol:          str
    strategy_name:   str
    direction:       SignalDirection
    confidence:      float          # 0.0 – 1.0
    technical_score: float          # 0.0 – 1.0
    indicators:      dict[str, Any] = field(default_factory=dict)
    explanation:     str  = ""
    timestamp:       datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_actionable(self) -> bool:
        """Only BUY/SELL with confidence > 0.5 are actionable."""
        return self.direction != SignalDirection.HOLD and self.confidence >= 0.5


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Subclasses must implement:
    - name: str  — unique strategy identifier (e.g. 'ema_crossover')
    - display_name: str
    - default_parameters: dict
    - _calculate(df, params) -> SignalResult
    """

    name:               str
    display_name:       str
    default_parameters: dict[str, Any]

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self.parameters = {**self.default_parameters, **(parameters or {})}

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        """
        Public entry point. Validates input then delegates to _calculate().
        Always returns a SignalResult — never raises.
        """
        if df is None or df.empty or len(df) < self._minimum_bars():
            return SignalResult(
                symbol=symbol,
                strategy_name=self.name,
                direction=SignalDirection.HOLD,
                confidence=0.0,
                technical_score=0.0,
                explanation=f"Insufficient data: need ≥ {self._minimum_bars()} bars",
            )
        try:
            df = df.copy()
            # Ensure correct column casing
            df.columns = [c.lower() for c in df.columns]
            return self._calculate(df, symbol)
        except Exception as exc:
            return SignalResult(
                symbol=symbol,
                strategy_name=self.name,
                direction=SignalDirection.HOLD,
                confidence=0.0,
                technical_score=0.0,
                explanation=f"Strategy error: {exc}",
            )

    @abstractmethod
    def _calculate(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        """Core strategy logic. df is pre-validated and column-normalized."""
        ...

    def _minimum_bars(self) -> int:
        """Override if strategy needs more than 60 bars."""
        return 60

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average Directional Index — measures trend strength."""
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low  - close.shift(1)).abs(),
        ], axis=1).max(axis=1)

        dm_plus  = (high - high.shift(1)).clip(lower=0)
        dm_minus = (low.shift(1) - low).clip(lower=0)
        dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)
        dm_minus = dm_minus.where(dm_minus > dm_plus, 0)

        atr   = tr.ewm(alpha=1/period, adjust=False).mean()
        di_p  = 100 * dm_plus.ewm(alpha=1/period, adjust=False).mean() / atr
        di_m  = 100 * dm_minus.ewm(alpha=1/period, adjust=False).mean() / atr
        dx    = (100 * (di_p - di_m).abs() / (di_p + di_m)).fillna(0)
        adx   = dx.ewm(alpha=1/period, adjust=False).mean()
        return adx

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = series.diff()
        gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
        loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
        rs    = gain / loss.replace(0, float("nan"))
        return 100 - 100 / (1 + rs)

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()
