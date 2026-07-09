"""
Mean Reversion Strategy (Bollinger Bands + Z-Score)

Signal logic:
  BUY  → Z-score < -2 (price > 2 std below mean) + price touching lower BB
           + ADX < threshold (sideways/low-vol regime — mean reversion works)
  SELL → Z-score > +2 (price > 2 std above mean) + price touching upper BB
           + ADX < threshold
  HOLD → Z-score within [-1.5, +1.5] OR strong trend (ADX > threshold)

IMPORTANT: Mean reversion FAILS in strong trends. ADX < adx_max is a hard gate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.strategies.base_strategy import BaseStrategy, SignalDirection, SignalResult


class MeanReversionStrategy(BaseStrategy):

    name         = "mean_reversion"
    display_name = "Mean Reversion (Bollinger Bands + Z-Score)"
    default_parameters = {
        "bb_period":          20,
        "bb_std":            2.0,   # Bollinger Band standard deviation multiplier
        "z_score_threshold": 2.0,   # |z| must exceed this to trigger
        "adx_max":           20,    # ADX must be BELOW this (sideways market)
        "adx_period":        14,
        "exit_z_score":      0.5,   # Exit position when z returns to this level
        "timeframe":        "1d",
    }

    def _minimum_bars(self) -> int:
        return self.parameters["bb_period"] + self.parameters["adx_period"] + 5

    def _calculate(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        p     = self.parameters
        close = df["close"]

        # ── Bollinger Bands ───────────────────────────────────────────────────
        bb_mid  = close.rolling(p["bb_period"]).mean()
        bb_std  = close.rolling(p["bb_period"]).std()
        bb_upper = bb_mid + p["bb_std"] * bb_std
        bb_lower = bb_mid - p["bb_std"] * bb_std
        bb_width = (bb_upper - bb_lower) / bb_mid   # normalized band width

        # ── Z-Score ───────────────────────────────────────────────────────────
        z_score = (close - bb_mid) / bb_std

        # ── ADX (trend strength — lower = more sideways) ──────────────────────
        adx = self._adx(df, p["adx_period"])

        # Current values (all from last completed bar — no look-ahead)
        curr_close  = close.iloc[-1]
        curr_z      = z_score.iloc[-1]
        curr_bb_up  = bb_upper.iloc[-1]
        curr_bb_lo  = bb_lower.iloc[-1]
        curr_bb_mid = bb_mid.iloc[-1]
        curr_bb_w   = bb_width.iloc[-1]
        curr_adx    = adx.iloc[-1]

        z_thresh    = p["z_score_threshold"]
        adx_max     = p["adx_max"]
        is_sideways = curr_adx < adx_max          # regime gate
        at_lower_bb = curr_close <= curr_bb_lo * 1.005  # price near lower band
        at_upper_bb = curr_close >= curr_bb_up * 0.995  # price near upper band

        # ── Signal logic ──────────────────────────────────────────────────────
        if curr_z < -z_thresh and at_lower_bb and is_sideways:
            direction = SignalDirection.BUY
            # More negative z = stronger signal
            z_strength = min(1.0, abs(curr_z) / (z_thresh * 2))
            confidence = min(0.88, 0.55 + z_strength * 0.33)

        elif curr_z > z_thresh and at_upper_bb and is_sideways:
            direction = SignalDirection.SELL
            z_strength = min(1.0, curr_z / (z_thresh * 2))
            confidence = min(0.88, 0.55 + z_strength * 0.33)

        elif not is_sideways and abs(curr_z) > z_thresh:
            # Z is extreme but we're in a TREND — don't fade the trend
            direction  = SignalDirection.HOLD
            confidence = 0.0

        else:
            direction  = SignalDirection.HOLD
            confidence = 0.0

        # ── Technical score ───────────────────────────────────────────────────
        z_score_contrib  = min(1.0, abs(curr_z) / (z_thresh * 1.5))
        regime_contrib   = max(0.0, 1.0 - curr_adx / adx_max) if is_sideways else 0.0
        technical_score  = (z_score_contrib * 0.65 + regime_contrib * 0.35)

        # Mean reversion target: return to midline
        reversion_target = round(float(curr_bb_mid), 4)
        reversion_pct    = round((reversion_target - curr_close) / curr_close * 100, 3)

        explanation = (
            f"Z-score={curr_z:.2f} "
            f"({'extreme low — mean reversion BUY' if curr_z < -z_thresh else 'extreme high — mean reversion SELL' if curr_z > z_thresh else 'within normal range'}). "
            f"ADX={curr_adx:.1f} ({'sideways ✅' if is_sideways else 'trending ❌ — strategy suspended'}). "
            f"BB: [{curr_bb_lo:.2f}, {curr_bb_mid:.2f}, {curr_bb_up:.2f}]. "
            f"Reversion target: {reversion_target} ({reversion_pct:+.2f}%)."
        )

        return SignalResult(
            symbol=symbol,
            strategy_name=self.name,
            direction=direction,
            confidence=round(confidence, 4),
            technical_score=round(technical_score, 4),
            indicators={
                "z_score":         round(float(curr_z), 3),
                "bb_upper":        round(float(curr_bb_up), 4),
                "bb_mid":          round(float(curr_bb_mid), 4),
                "bb_lower":        round(float(curr_bb_lo), 4),
                "bb_width":        round(float(curr_bb_w), 4),
                "adx":             round(float(curr_adx), 2),
                "is_sideways":     is_sideways,
                "at_lower_bb":     at_lower_bb,
                "at_upper_bb":     at_upper_bb,
                "reversion_target": reversion_target,
                "reversion_pct":   reversion_pct,
            },
            explanation=explanation,
        )
