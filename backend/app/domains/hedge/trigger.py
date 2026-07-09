"""
Hedge Trigger Engine

Continuously evaluates portfolio risk and determines WHEN to hedge.
Uses dynamic, proportional triggers — NOT binary on/off.

Trigger sources:
  1. VIX level (volatility regime)
  2. Portfolio drawdown from peak
  3. Portfolio beta exceeds cap
  4. Single position loss exceeds threshold
  5. Manual trigger (user-initiated)

Dynamic hedge scaling:
  Low stress  → hedge ratio 0.0 (no hedge needed)
  Caution     → hedge ratio 0.25 (light hedge)
  High stress → hedge ratio 0.50 (moderate hedge)
  Extreme     → hedge ratio 1.00 (full beta-neutral)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.config import settings


class TriggerType(str, Enum):
    VIX_THRESHOLD   = "vix_threshold"
    DRAWDOWN        = "drawdown"
    BETA_EXCEEDED   = "beta_exceeded"
    POSITION_LOSS   = "position_loss"
    MANUAL          = "manual"
    NONE            = "none"


class VolatilityRegime(str, Enum):
    LOW      = "low"       # VIX < 15
    NORMAL   = "normal"    # VIX 15–20
    CAUTION  = "caution"   # VIX 20–25
    HIGH     = "high"      # VIX 25–30
    EXTREME  = "extreme"   # VIX > 30


@dataclass
class HedgeTriggerResult:
    should_hedge:    bool
    trigger_type:    TriggerType
    trigger_value:   float
    trigger_threshold: float
    hedge_ratio:     float   # 0.0–1.0 — how aggressively to hedge
    regime:          VolatilityRegime
    explanation:     str


# ── Regime Classification ─────────────────────────────────────────────────────

def classify_regime(vix: float) -> VolatilityRegime:
    if vix < 15:   return VolatilityRegime.LOW
    if vix < 20:   return VolatilityRegime.NORMAL
    if vix < 25:   return VolatilityRegime.CAUTION
    if vix < 30:   return VolatilityRegime.HIGH
    return VolatilityRegime.EXTREME


# Position scaling by regime (used to size new trades)
REGIME_POSITION_SCALE = {
    VolatilityRegime.LOW:     1.25,
    VolatilityRegime.NORMAL:  1.00,
    VolatilityRegime.CAUTION: 0.75,
    VolatilityRegime.HIGH:    0.50,
    VolatilityRegime.EXTREME: 0.25,
}

# Hedge ratio by regime (what fraction of beta exposure to hedge)
REGIME_HEDGE_RATIO = {
    VolatilityRegime.LOW:     0.00,
    VolatilityRegime.NORMAL:  0.00,
    VolatilityRegime.CAUTION: 0.25,
    VolatilityRegime.HIGH:    0.60,
    VolatilityRegime.EXTREME: 1.00,
}


# ── Main Trigger Evaluation ───────────────────────────────────────────────────

def evaluate_hedge_triggers(
    vix:                  float,
    portfolio_drawdown:   float,   # negative decimal, e.g. -0.07
    portfolio_beta:       float,
    largest_position_loss: float,  # negative decimal of worst position
    thresholds:           dict | None = None,
) -> HedgeTriggerResult:
    """
    Evaluate all hedge triggers and return recommended action.
    Checks triggers in priority order — returns first that fires.
    """
    t = thresholds or {}
    vix_caution   = t.get("vix_caution_level",    settings.vix_caution_level)
    vix_hedge     = t.get("vix_hedge_level",       settings.vix_hedge_level)
    vix_extreme   = t.get("vix_aggressive_level",  settings.vix_aggressive_level)
    max_drawdown  = t.get("max_drawdown_trigger",  settings.max_drawdown_trigger)
    max_beta      = t.get("max_position_beta",     settings.max_position_beta)
    pos_loss_lim  = t.get("single_position_loss",  settings.single_position_loss_trigger)

    regime = classify_regime(vix)

    # ── Priority 1: Extreme VIX ───────────────────────────────────────────────
    if vix >= vix_extreme:
        return HedgeTriggerResult(
            should_hedge=True,
            trigger_type=TriggerType.VIX_THRESHOLD,
            trigger_value=vix,
            trigger_threshold=vix_extreme,
            hedge_ratio=REGIME_HEDGE_RATIO[regime],
            regime=regime,
            explanation=(
                f"EXTREME volatility: VIX {vix:.1f} ≥ {vix_extreme:.0f}. "
                f"Full hedge activated. Recommend {REGIME_HEDGE_RATIO[regime]:.0%} "
                f"beta neutralization via inverse ETFs."
            ),
        )

    # ── Priority 2: High portfolio drawdown ───────────────────────────────────
    if abs(portfolio_drawdown) >= max_drawdown:
        hedge_ratio = min(1.0, abs(portfolio_drawdown) / (max_drawdown * 2))
        return HedgeTriggerResult(
            should_hedge=True,
            trigger_type=TriggerType.DRAWDOWN,
            trigger_value=portfolio_drawdown,
            trigger_threshold=-max_drawdown,
            hedge_ratio=hedge_ratio,
            regime=regime,
            explanation=(
                f"Portfolio drawdown {abs(portfolio_drawdown):.1%} exceeds "
                f"limit {max_drawdown:.1%}. "
                f"Hedging {hedge_ratio:.0%} of beta exposure."
            ),
        )

    # ── Priority 3: Elevated VIX (caution zone) ───────────────────────────────
    if vix >= vix_hedge:
        return HedgeTriggerResult(
            should_hedge=True,
            trigger_type=TriggerType.VIX_THRESHOLD,
            trigger_value=vix,
            trigger_threshold=vix_hedge,
            hedge_ratio=REGIME_HEDGE_RATIO[regime],
            regime=regime,
            explanation=(
                f"Elevated volatility: VIX {vix:.1f} ≥ {vix_hedge:.0f}. "
                f"Partial hedge: {REGIME_HEDGE_RATIO[regime]:.0%} of beta exposure."
            ),
        )

    # ── Priority 4: Portfolio beta too high ───────────────────────────────────
    if portfolio_beta > max_beta:
        excess_beta = portfolio_beta - max_beta
        hedge_ratio = min(1.0, excess_beta / max_beta)
        return HedgeTriggerResult(
            should_hedge=True,
            trigger_type=TriggerType.BETA_EXCEEDED,
            trigger_value=portfolio_beta,
            trigger_threshold=max_beta,
            hedge_ratio=hedge_ratio,
            regime=regime,
            explanation=(
                f"Portfolio beta {portfolio_beta:.2f} exceeds cap {max_beta:.2f}. "
                f"Hedging excess beta of {excess_beta:.2f} (~{hedge_ratio:.0%} of exposure)."
            ),
        )

    # ── Priority 5: Single position catastrophic loss ─────────────────────────
    if abs(largest_position_loss) >= pos_loss_lim:
        return HedgeTriggerResult(
            should_hedge=True,
            trigger_type=TriggerType.POSITION_LOSS,
            trigger_value=largest_position_loss,
            trigger_threshold=-pos_loss_lim,
            hedge_ratio=0.30,
            regime=regime,
            explanation=(
                f"Single position loss {abs(largest_position_loss):.1%} exceeds "
                f"threshold {pos_loss_lim:.1%}. "
                f"Light hedge (30%) to protect remaining portfolio."
            ),
        )

    # ── No trigger fired ─────────────────────────────────────────────────────
    return HedgeTriggerResult(
        should_hedge=False,
        trigger_type=TriggerType.NONE,
        trigger_value=vix,
        trigger_threshold=vix_caution,
        hedge_ratio=0.0,
        regime=regime,
        explanation=(
            f"No hedge triggers active. VIX={vix:.1f} ({regime.value}), "
            f"beta={portfolio_beta:.2f}, drawdown={portfolio_drawdown:.1%}. "
            f"Portfolio monitoring normal."
        ),
    )


def get_position_scale(vix: float) -> float:
    """
    How much to scale position sizes based on current VIX regime.
    Called before placing any new trade.
    """
    regime = classify_regime(vix)
    return REGIME_POSITION_SCALE[regime]
