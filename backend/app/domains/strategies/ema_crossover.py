"""
EMA Crossover Strategy (Trend Following)

Signal logic:
  BUY  → EMA fast crosses ABOVE EMA slow + ADX > threshold (trending up)
  SELL → EMA fast crosses BELOW EMA slow + ADX > threshold (trending down)
  HOLD → Crossover absent OR ADX < threshold (ranging market, no entry)

Best timeframes: daily (1d), 4-hour (4h)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.strategies.base_strategy import BaseStrategy, SignalDirection, SignalResult


class EMACrossoverStrategy(BaseStrategy):

    name         = "ema_crossover"
    display_name = "EMA Crossover (Trend Following)"
    default_parameters = {
        "fast_period":    20,
        "slow_period":    50,
        "adx_period":     14,
        "adx_threshold":  25,   # ADX must be > this to confirm trend strength
        "timeframe":     "1d",
    }

    def _minimum_bars(self) -> int:
        return self.parameters["slow_period"] + self.parameters["adx_period"] + 5

    def _calculate(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        p = self.parameters
        fast = p["fast_period"]
        slow = p["slow_period"]
        adx_thresh = p["adx_threshold"]

        close = df["close"]

        # ── Indicators ────────────────────────────────────────────────────────
        ema_fast = self._ema(close, fast)
        ema_slow = self._ema(close, slow)
        adx      = self._adx(df, p["adx_period"])

        # Crossover detection: compare current vs previous bar
        # CRITICAL: use shift(1) to avoid look-ahead bias
        prev_fast = ema_fast.shift(1)
        prev_slow = ema_slow.shift(1)

        curr_fast = ema_fast.iloc[-1]
        curr_slow = ema_slow.iloc[-1]
        last_prev_fast = prev_fast.iloc[-1]
        last_prev_slow = prev_slow.iloc[-1]
        curr_adx  = adx.iloc[-1]

        golden_cross = (curr_fast > curr_slow) and (last_prev_fast <= last_prev_slow)
        death_cross  = (curr_fast < curr_slow) and (last_prev_fast >= last_prev_slow)
        trend_up     = curr_fast > curr_slow
        trend_down   = curr_fast < curr_slow
        adx_confirms = curr_adx >= adx_thresh

        # ── Signal logic ──────────────────────────────────────────────────────
        if golden_cross and adx_confirms:
            direction = SignalDirection.BUY
            # Strong fresh crossover: high confidence
            confidence = min(0.95, 0.70 + (curr_adx - adx_thresh) / 100)
        elif death_cross and adx_confirms:
            direction = SignalDirection.SELL
            confidence = min(0.95, 0.70 + (curr_adx - adx_thresh) / 100)
        elif trend_up and adx_confirms:
            # No fresh cross but in uptrend — weaker buy signal
            direction = SignalDirection.BUY
            ema_separation = abs(curr_fast - curr_slow) / curr_slow
            confidence = min(0.65, 0.40 + ema_separation * 10)
        elif trend_down and adx_confirms:
            direction = SignalDirection.SELL
            ema_separation = abs(curr_fast - curr_slow) / curr_slow
            confidence = min(0.65, 0.40 + ema_separation * 10)
        else:
            direction  = SignalDirection.HOLD
            confidence = 0.0

        # ── Technical score (0–1, independent of direction) ──────────────────
        adx_score = min(1.0, curr_adx / 50)
        separation_score = min(1.0, abs(curr_fast - curr_slow) / curr_slow * 20)
        technical_score = (adx_score * 0.6 + separation_score * 0.4)

        explanation = (
            f"EMA{fast}={curr_fast:.2f} {'>' if trend_up else '<'} EMA{slow}={curr_slow:.2f}. "
            f"ADX={curr_adx:.1f} ({'confirms trend' if adx_confirms else 'below threshold — ranging market'}). "
            f"{'🟢 Golden cross detected.' if golden_cross else '🔴 Death cross detected.' if death_cross else ''}"
        )

        return SignalResult(
            symbol=symbol,
            strategy_name=self.name,
            direction=direction,
            confidence=round(confidence, 4),
            technical_score=round(technical_score, 4),
            indicators={
                "ema_fast": round(float(curr_fast), 4),
                "ema_slow": round(float(curr_slow), 4),
                "adx": round(float(curr_adx), 2),
                "golden_cross": golden_cross,
                "death_cross": death_cross,
                "adx_confirms": adx_confirms,
                "ema_separation_pct": round(abs(curr_fast - curr_slow) / curr_slow * 100, 3),
            },
            explanation=explanation,
        )
