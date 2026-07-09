"""
Signal Aggregator — combines signals from all active strategies into one
unified recommendation with a weighted confidence score.

Aggregation method: weighted voting
- Each strategy votes BUY (+1), SELL (-1), or HOLD (0)
- Votes are weighted by strategy confidence × strategy weight
- Final direction determined by net vote score
- Final confidence = |net_score| / max_possible_score
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.strategies.base_strategy import SignalDirection, SignalResult


# Default weights per strategy (must sum to 1.0)
STRATEGY_WEIGHTS: dict[str, float] = {
    "ema_crossover": 0.40,
    "rsi_momentum":  0.35,
    "mean_reversion": 0.25,
}


@dataclass
class AggregatedSignal:
    """Unified signal combining all active strategy outputs."""
    symbol:           str
    direction:        SignalDirection
    confidence:       float          # 0.0 – 1.0
    agreement_ratio:  float          # % of strategies agreeing
    contributing:     list[dict]     # per-strategy breakdown
    net_score:        float          # raw weighted vote score
    explanation:      str


def aggregate_signals(
    signals: list[SignalResult],
    weights: dict[str, float] | None = None,
    min_confidence: float = 0.45,
    min_agreement:  float = 0.50,
) -> AggregatedSignal:
    """
    Aggregate multiple strategy signals into a single recommendation.

    Args:
        signals:        List of SignalResult from each active strategy
        weights:        Strategy weight overrides (default: STRATEGY_WEIGHTS)
        min_confidence: Minimum confidence to produce BUY/SELL (else HOLD)
        min_agreement:  Minimum fraction of strategies that must agree

    Returns:
        AggregatedSignal with unified direction and confidence
    """
    weights = weights or STRATEGY_WEIGHTS

    if not signals:
        return _hold_signal("", "No active strategies")

    symbol = signals[0].symbol
    active_strategies = [s.strategy_name for s in signals]

    # ── Normalize weights to only active strategies ───────────────────────────
    active_weights = {
        name: w for name, w in weights.items() if name in active_strategies
    }
    total_w = sum(active_weights.values())
    if total_w == 0:
        return _hold_signal(symbol, "No weighted strategies active")
    norm_weights = {k: v / total_w for k, v in active_weights.items()}

    # ── Weighted vote ─────────────────────────────────────────────────────────
    # +1 = BUY, -1 = SELL, 0 = HOLD
    direction_map = {
        SignalDirection.BUY:  +1.0,
        SignalDirection.SELL: -1.0,
        SignalDirection.HOLD:  0.0,
    }

    net_score = 0.0
    buy_votes  = 0
    sell_votes = 0
    hold_votes = 0
    contributing = []

    for sig in signals:
        w    = norm_weights.get(sig.strategy_name, 0.0)
        vote = direction_map[sig.direction]
        weighted_vote = w * sig.confidence * vote

        net_score += weighted_vote

        if sig.direction == SignalDirection.BUY:
            buy_votes += 1
        elif sig.direction == SignalDirection.SELL:
            sell_votes += 1
        else:
            hold_votes += 1

        contributing.append({
            "strategy":       sig.strategy_name,
            "direction":      sig.direction.value,
            "confidence":     sig.confidence,
            "weight":         round(w, 3),
            "weighted_vote":  round(weighted_vote, 4),
            "technical_score": sig.technical_score,
        })

    total_signals = len(signals)
    max_agreeing  = max(buy_votes, sell_votes, hold_votes)
    agreement_ratio = max_agreeing / total_signals

    # ── Determine final direction ─────────────────────────────────────────────
    # Net score > 0 = bullish lean, < 0 = bearish lean
    abs_score  = abs(net_score)
    final_confidence = min(0.97, abs_score * 1.5)  # scale to 0-1

    if (
        abs_score >= min_confidence * 0.5
        and agreement_ratio >= min_agreement
        and final_confidence >= min_confidence
    ):
        direction = SignalDirection.BUY if net_score > 0 else SignalDirection.SELL
    else:
        direction = SignalDirection.HOLD
        final_confidence = 0.0

    # ── Human-readable explanation ────────────────────────────────────────────
    vote_summary = f"BUY:{buy_votes} SELL:{sell_votes} HOLD:{hold_votes}"
    explanation = (
        f"Aggregated {total_signals} strategies ({vote_summary}). "
        f"Net weighted score: {net_score:+.3f}. "
        f"Agreement: {agreement_ratio:.0%}. "
        f"{'Signal confirmed.' if direction != SignalDirection.HOLD else 'Insufficient consensus — holding.'}"
    )

    return AggregatedSignal(
        symbol=symbol,
        direction=direction,
        confidence=round(final_confidence, 4),
        agreement_ratio=round(agreement_ratio, 3),
        contributing=contributing,
        net_score=round(net_score, 4),
        explanation=explanation,
    )


def _hold_signal(symbol: str, reason: str) -> AggregatedSignal:
    return AggregatedSignal(
        symbol=symbol,
        direction=SignalDirection.HOLD,
        confidence=0.0,
        agreement_ratio=0.0,
        contributing=[],
        net_score=0.0,
        explanation=reason,
    )
