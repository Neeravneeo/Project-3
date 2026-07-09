"""
Hedge Recommender — computes exact hedge instrument and quantity.

Given a trigger result, calculates:
  1. Which instrument to use (SH / SDS / PSQ)
  2. How many shares to buy
  3. Expected beta reduction
  4. Estimated hedge cost

Hedge instruments:
  SH  → 1x inverse S&P 500 (beta ≈ -1.0) — gentle, liquid
  SDS → 2x inverse S&P 500 (beta ≈ -2.0) — moderate
  PSQ → 1x inverse NASDAQ  (beta ≈ -1.0) — tech-heavy portfolios

IMPORTANT: Avoid VIX instruments (VXX/UVXY) — suffer severe contango bleed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.hedge.trigger import HedgeTriggerResult, VolatilityRegime


# Instrument betas (approximate, updated periodically)
HEDGE_INSTRUMENTS = {
    "SH":  {"beta": -1.0, "description": "ProShares Short S&P500 (1x inverse)"},
    "SDS": {"beta": -2.0, "description": "ProShares UltraShort S&P500 (2x inverse)"},
    "PSQ": {"beta": -1.0, "description": "ProShares Short QQQ (1x inverse NASDAQ)"},
}

# Regime → preferred instrument
REGIME_INSTRUMENT = {
    VolatilityRegime.CAUTION: "SH",    # light, liquid
    VolatilityRegime.HIGH:    "SH",    # still prefer 1x to avoid leverage bleed
    VolatilityRegime.EXTREME: "SDS",   # need more punch in crashes
}


@dataclass
class HedgeRecommendation:
    instrument:          str
    instrument_beta:     float
    shares:              int
    estimated_cost:      float    # $
    beta_reduction:      float    # how much portfolio beta drops
    new_portfolio_beta:  float
    hedge_effectiveness: float    # % of target achieved (0–1)
    explanation:         str


def compute_hedge_recommendation(
    trigger:              HedgeTriggerResult,
    portfolio_value:      float,
    portfolio_beta:       float,
    instrument_prices:    dict[str, float],   # {"SH": 14.20, "SDS": 34.50, "PSQ": 11.80}
    target_beta:          float = 0.0,        # 0.0 = fully market neutral
    tech_weight:          float = 0.0,        # portfolio fraction in tech (use PSQ if > 40%)
) -> HedgeRecommendation | None:
    """
    Calculate the optimal hedge trade.
    Returns None if hedge_ratio is 0 or portfolio_value is too small.
    """
    if not trigger.should_hedge or trigger.hedge_ratio == 0.0:
        return None

    if portfolio_value < 1000:
        return None

    # ── Choose instrument ─────────────────────────────────────────────────────
    # Use PSQ if portfolio is tech-heavy
    if tech_weight >= 0.40:
        instrument = "PSQ"
    else:
        instrument = REGIME_INSTRUMENT.get(trigger.regime, "SH")

    inst_beta  = HEDGE_INSTRUMENTS[instrument]["beta"]
    inst_price = instrument_prices.get(instrument)
    if not inst_price or inst_price <= 0:
        # Fallback: try any available instrument
        for sym, price in instrument_prices.items():
            if price and price > 0 and sym in HEDGE_INSTRUMENTS:
                instrument = sym
                inst_beta  = HEDGE_INSTRUMENTS[sym]["beta"]
                inst_price = price
                break
        else:
            return None

    # ── Calculate hedge size ───────────────────────────────────────────────────
    # Formula: hedge_value = portfolio_value × portfolio_beta × hedge_ratio
    # Shares = hedge_value / (instrument_price × |instrument_beta|)
    hedge_value = portfolio_value * portfolio_beta * trigger.hedge_ratio
    raw_shares  = hedge_value / (inst_price * abs(inst_beta))
    shares      = max(1, round(raw_shares))
    actual_cost = shares * inst_price

    # ── Expected beta impact ──────────────────────────────────────────────────
    # Hedge beta contribution = (hedge_value / portfolio_value) × instrument_beta
    hedge_beta_contribution = (actual_cost / portfolio_value) * inst_beta
    new_beta = portfolio_beta + hedge_beta_contribution
    beta_reduction = portfolio_beta - new_beta

    # Effectiveness: how close to target_beta did we get?
    distance_before = abs(portfolio_beta - target_beta)
    distance_after  = abs(new_beta - target_beta)
    effectiveness   = 1.0 - (distance_after / distance_before) if distance_before > 0 else 1.0

    explanation = (
        f"Recommend: BUY {shares} shares of {instrument} @ ${inst_price:.2f} "
        f"(cost: ${actual_cost:,.2f}). "
        f"Portfolio beta: {portfolio_beta:.2f} → {new_beta:.2f} "
        f"({beta_reduction:.2f} reduction, {effectiveness:.0%} effective). "
        f"Instrument: {HEDGE_INSTRUMENTS[instrument]['description']}."
    )

    return HedgeRecommendation(
        instrument=instrument,
        instrument_beta=inst_beta,
        shares=shares,
        estimated_cost=round(actual_cost, 2),
        beta_reduction=round(beta_reduction, 4),
        new_portfolio_beta=round(new_beta, 4),
        hedge_effectiveness=round(effectiveness, 4),
        explanation=explanation,
    )


def should_rehedge(
    current_beta:  float,
    target_beta:   float = 0.0,
    last_beta:     float | None = None,
    drift_threshold: float = 0.15,
) -> bool:
    """
    Check if existing hedge needs rebalancing.
    Rehedge if beta has drifted > drift_threshold from target.
    """
    if abs(current_beta - target_beta) > drift_threshold:
        return True
    if last_beta is not None and abs(current_beta - last_beta) > drift_threshold:
        return True
    return False
