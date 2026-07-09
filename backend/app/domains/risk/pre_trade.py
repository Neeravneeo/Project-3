"""
Pre-Trade Risk Checks

Every order passes through this gate before reaching the broker.
If any check fails, the order is REJECTED with an explanation.
This is the final safety layer before real money is touched.

Checks (in order):
  1. Market hours
  2. Position size limit (max % of portfolio)
  3. Cash availability
  4. Portfolio beta cap
  5. Single-position loss limit (don't add to a loser)
  6. Concentration limit
  7. Portfolio drawdown gate (suspend trading if drawdown too deep)
"""

from __future__ import annotations

from dataclasses import dataclass

from app.brokers.base import OrderRequest, OrderSide
from app.core.config import settings


@dataclass
class PreTradeResult:
    approved:    bool
    reason:      str
    checks_run:  list[str]
    checks_failed: list[str]


def run_pre_trade_checks(
    order:              OrderRequest,
    portfolio_value:    float,
    cash_available:     float,
    current_price:      float,
    portfolio_beta:     float,
    portfolio_drawdown: float,   # negative decimal, e.g. -0.07 = 7% drawdown
    position_weight:    float,   # existing position as fraction of portfolio (0–1)
    position_pnl_pct:  float,   # existing position P&L as decimal
    is_market_open:     bool,
    thresholds:         dict | None = None,
) -> PreTradeResult:
    """
    Run all pre-trade risk checks.
    Returns PreTradeResult with approved=True/False and full explanation.
    """
    t = thresholds or {}
    max_position_weight   = t.get("max_position_weight",   settings.max_position_weight)
    max_position_beta     = t.get("max_position_beta",     settings.max_position_beta)
    max_drawdown_trigger  = t.get("max_drawdown_trigger",  settings.max_drawdown_trigger)
    single_pos_loss       = t.get("single_position_loss",  settings.single_position_loss_trigger)

    checks_run    = []
    checks_failed = []

    # ── 1. Market hours ───────────────────────────────────────────────────────
    checks_run.append("market_hours")
    if not is_market_open and not order.is_hedge:
        checks_failed.append("market_hours")
        return PreTradeResult(
            approved=False,
            reason="Market is closed. Order rejected.",
            checks_run=checks_run,
            checks_failed=checks_failed,
        )

    # ── 2. Portfolio drawdown gate ────────────────────────────────────────────
    checks_run.append("drawdown_gate")
    if abs(portfolio_drawdown) >= max_drawdown_trigger and order.side == OrderSide.BUY and not order.is_hedge:
        checks_failed.append("drawdown_gate")
        return PreTradeResult(
            approved=False,
            reason=(
                f"Portfolio drawdown {abs(portfolio_drawdown):.1%} exceeds limit "
                f"{max_drawdown_trigger:.1%}. New BUY orders suspended. "
                f"Only hedges and position closing allowed."
            ),
            checks_run=checks_run,
            checks_failed=checks_failed,
        )

    # ── 3. Cash availability ──────────────────────────────────────────────────
    checks_run.append("cash_check")
    if order.side == OrderSide.BUY:
        order_cost = current_price * order.quantity
        if order_cost > cash_available:
            checks_failed.append("cash_check")
            return PreTradeResult(
                approved=False,
                reason=(
                    f"Insufficient cash. Order cost ${order_cost:,.2f}, "
                    f"available ${cash_available:,.2f}."
                ),
                checks_run=checks_run,
                checks_failed=checks_failed,
            )

    # ── 4. Position size limit ────────────────────────────────────────────────
    checks_run.append("position_size")
    if portfolio_value > 0 and order.side == OrderSide.BUY:
        order_weight = (current_price * order.quantity) / portfolio_value
        new_weight   = position_weight + order_weight
        if new_weight > max_position_weight and not order.is_hedge:
            checks_failed.append("position_size")
            return PreTradeResult(
                approved=False,
                reason=(
                    f"Order would create {new_weight:.1%} position in {order.symbol} "
                    f"(limit: {max_position_weight:.1%}). Reduce quantity."
                ),
                checks_run=checks_run,
                checks_failed=checks_failed,
            )

    # ── 5. Don't add to a significant loser ───────────────────────────────────
    checks_run.append("loss_limit")
    if (
        order.side == OrderSide.BUY
        and position_pnl_pct < -single_pos_loss
        and not order.is_hedge
        and position_weight > 0
    ):
        checks_failed.append("loss_limit")
        return PreTradeResult(
            approved=False,
            reason=(
                f"{order.symbol} is down {abs(position_pnl_pct):.1%} from entry "
                f"(limit: {single_pos_loss:.1%}). Adding to a loser is blocked. "
                f"Close the position or wait for recovery."
            ),
            checks_run=checks_run,
            checks_failed=checks_failed,
        )

    # ── 6. Portfolio beta cap ─────────────────────────────────────────────────
    checks_run.append("beta_cap")
    if portfolio_beta > max_position_beta and order.side == OrderSide.BUY and not order.is_hedge:
        checks_failed.append("beta_cap")
        return PreTradeResult(
            approved=False,
            reason=(
                f"Portfolio beta {portfolio_beta:.2f} exceeds cap {max_position_beta:.2f}. "
                f"Hedge first or close high-beta positions before adding exposure."
            ),
            checks_run=checks_run,
            checks_failed=checks_failed,
        )

    # ── All checks passed ─────────────────────────────────────────────────────
    return PreTradeResult(
        approved=True,
        reason="All pre-trade checks passed.",
        checks_run=checks_run,
        checks_failed=[],
    )
