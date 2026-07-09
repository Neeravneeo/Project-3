"""
RSI Momentum Strategy

Signal logic:
  BUY  → RSI crosses above 30 (oversold recovery) OR RSI > 50 with ROC trending up
  SELL → RSI crosses below 70 (overbought reversal) OR RSI < 50 with ROC trending down
  HOLD → RSI in neutral zone without clear momentum

ATR-based stop loss included in indicators for position sizing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.strategies.base_strategy import BaseStrategy, SignalDirection, SignalResult


class RSIMomentumStrategy(BaseStrategy):

    name         = "rsi_momentum"
    display_name = "RSI Momentum"
    default_parameters = {
        "rsi_period":   14,
        "oversold":     30,
        "overbought":   70,
        "roc_period":   12,    # Rate of Change lookback
        "atr_period":   14,
        "atr_multiplier": 2.0, # Stop loss = entry - (atr_mult * ATR)
        "timeframe":   "1d",
    }

    def _minimum_bars(self) -> int:
        return max(self.parameters["rsi_period"], self.parameters["roc_period"]) + 10

    def _calculate(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        p          = self.parameters
        close      = df["close"]

        # ── Indicators ────────────────────────────────────────────────────────
        rsi = self._rsi(close, p["rsi_period"])

        # Rate of Change: % price change over n periods
        roc = close.pct_change(p["roc_period"]) * 100

        # ATR for stop-loss calculation
        high, low = df["high"], df["low"]
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low  - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / p["atr_period"], adjust=False).mean()

        curr_rsi  = rsi.iloc[-1]
        prev_rsi  = rsi.iloc[-2]
        curr_roc  = roc.iloc[-1]
        curr_atr  = atr.iloc[-1]
        curr_close = close.iloc[-1]

        oversold    = p["oversold"]
        overbought  = p["overbought"]

        # ── Crossover detection (look-ahead safe — uses shift implicitly) ─────
        rsi_cross_up   = prev_rsi <= oversold  and curr_rsi > oversold   # oversold recovery
        rsi_cross_down = prev_rsi >= overbought and curr_rsi < overbought # overbought reversal

        # Momentum-style: RSI > 50 + positive ROC = riding the trend
        momentum_bull = curr_rsi > 55 and curr_roc > 0
        momentum_bear = curr_rsi < 45 and curr_roc < 0

        # ── Signal + confidence ───────────────────────────────────────────────
        if rsi_cross_up:
            direction  = SignalDirection.BUY
            # Stronger signal the more oversold it was
            confidence = min(0.92, 0.65 + (oversold - prev_rsi) / 50)
        elif rsi_cross_down:
            direction  = SignalDirection.SELL
            confidence = min(0.92, 0.65 + (prev_rsi - overbought) / 50)
        elif momentum_bull:
            direction  = SignalDirection.BUY
            rsi_score  = (curr_rsi - 50) / 50
            roc_score  = min(1.0, curr_roc / 10)
            confidence = min(0.75, 0.45 + (rsi_score + roc_score) / 4)
        elif momentum_bear:
            direction  = SignalDirection.SELL
            rsi_score  = (50 - curr_rsi) / 50
            roc_score  = min(1.0, abs(curr_roc) / 10)
            confidence = min(0.75, 0.45 + (rsi_score + roc_score) / 4)
        else:
            direction  = SignalDirection.HOLD
            confidence = 0.0

        # ── Technical score ───────────────────────────────────────────────────
        rsi_extremity = abs(curr_rsi - 50) / 50       # 0 at neutral, 1 at extreme
        roc_strength  = min(1.0, abs(curr_roc) / 10)
        technical_score = (rsi_extremity * 0.6 + roc_strength * 0.4)

        # Stop loss level (below current price by ATR * multiplier)
        stop_loss = curr_close - (p["atr_multiplier"] * curr_atr)

        explanation = (
            f"RSI={curr_rsi:.1f} "
            f"({'oversold recovery' if rsi_cross_up else 'overbought reversal' if rsi_cross_down else 'neutral'}). "
            f"ROC({p['roc_period']})={curr_roc:.2f}%. "
            f"ATR={curr_atr:.2f}, suggested stop @ {stop_loss:.2f}."
        )

        return SignalResult(
            symbol=symbol,
            strategy_name=self.name,
            direction=direction,
            confidence=round(confidence, 4),
            technical_score=round(technical_score, 4),
            indicators={
                "rsi": round(float(curr_rsi), 2),
                "rsi_prev": round(float(prev_rsi), 2),
                "roc": round(float(curr_roc), 3),
                "atr": round(float(curr_atr), 4),
                "stop_loss": round(float(stop_loss), 4),
                "rsi_cross_up":   rsi_cross_up,
                "rsi_cross_down": rsi_cross_down,
                "momentum_bull":  momentum_bull,
                "momentum_bear":  momentum_bear,
            },
            explanation=explanation,
        )
