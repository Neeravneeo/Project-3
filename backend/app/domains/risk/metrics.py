"""
Risk Metrics Engine

All research-validated formulas from the implementation plan.
Every function is pure (no side effects) — takes pandas Series, returns float.
Used by: risk API, pre-trade checks, post-trade monitoring, Celery snapshots.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy import stats


# ── Core Return Metrics ───────────────────────────────────────────────────────

def sharpe_ratio(returns: pd.Series, risk_free: float = 0.045, periods: int = 252) -> float:
    """
    Annualized Sharpe Ratio.
    risk_free: annual rate (US 10yr ~4.5%, India 10yr ~6.5%)
    periods:   252 for daily, 52 for weekly, 12 for monthly
    """
    if returns.empty or len(returns) <= 1:
        return 0.0
    std = float(returns.std())
    if np.isnan(std) or std <= 1e-12:
        return 0.0
    excess = returns - (risk_free / periods)
    excess_std = float(excess.std())
    return float(np.sqrt(periods) * float(excess.mean()) / excess_std)


def sortino_ratio(returns: pd.Series, risk_free: float = 0.045, periods: int = 252) -> float:
    """
    Sortino Ratio — penalizes only downside volatility.
    Superior to Sharpe for asymmetric return distributions.
    """
    if returns.empty or len(returns) <= 1:
        return 0.0
    downside = returns[returns < 0]
    if downside.empty:
        return float("inf") if annualized_return(returns, periods) > risk_free else 0.0
    downside_std = float(np.sqrt((downside ** 2).mean()) * np.sqrt(periods))
    if np.isnan(downside_std) or downside_std <= 1e-12:
        return float("inf") if annualized_return(returns, periods) > risk_free else 0.0
    excess = returns - (risk_free / periods)
    return float(excess.mean() * periods / downside_std)


def max_drawdown(returns: pd.Series) -> float:
    """
    Maximum drawdown from peak (returns negative number).
    e.g. -0.25 = 25% drawdown
    """
    if returns.empty:
        return 0.0
    cum = (1 + returns).cumprod()
    peak = cum.cummax()
    dd = np.where(peak > 1e-12, (cum - peak) / peak, -1.0)
    return float(np.min(dd))


def calmar_ratio(returns: pd.Series, periods: int = 252) -> float:
    """
    Calmar Ratio = Annualized Return / |Max Drawdown|
    Higher is better. < 0.5 = poor, > 1.0 = good.
    """
    if returns.empty or len(returns) <= 1:
        return 0.0
    mdd = abs(max_drawdown(returns))
    ann_ret = annualized_return(returns, periods)
    if np.isnan(mdd) or mdd <= 1e-12:
        return float("inf") if ann_ret > 0 else 0.0
    return float(ann_ret / mdd)


def annualized_return(returns: pd.Series, periods: int = 252) -> float:
    """Compound annualized return."""
    if returns.empty:
        return 0.0
    return float((1 + returns.mean()) ** periods - 1)


def annualized_volatility(returns: pd.Series, periods: int = 252) -> float:
    """Annualized standard deviation of returns."""
    if returns.empty or len(returns) <= 1:
        return 0.0
    std = float(returns.std())
    if np.isnan(std) or std <= 1e-12:
        return 0.0
    return float(std * np.sqrt(periods))


def win_rate(returns: pd.Series) -> float:
    """Fraction of periods with positive return."""
    if returns.empty:
        return 0.0
    return float((returns > 0).sum() / len(returns))


# ── Value at Risk ─────────────────────────────────────────────────────────────

def var_historical(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical VaR at given confidence level.
    Returns negative number: e.g. -0.018 = 1.8% loss at 95% confidence.
    Non-parametric — no distribution assumptions.
    """
    if returns.empty:
        return 0.0
    return float(np.percentile(returns, (1 - confidence) * 100))


def var_parametric(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Parametric VaR assuming normal distribution.
    Less accurate for fat-tailed financial returns.
    """
    if returns.empty or len(returns) <= 1:
        return 0.0
    std = float(returns.std())
    if np.isnan(std) or std <= 1e-12:
        return 0.0
    return float(stats.norm.ppf(1 - confidence, float(returns.mean()), std))


def cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Conditional VaR / Expected Shortfall.
    Average loss given that loss exceeds VaR.
    More conservative and informative than VaR alone.
    """
    if returns.empty:
        return 0.0
    var = var_historical(returns, confidence)
    tail = returns[returns <= var]
    return float(tail.mean()) if not tail.empty else var


def var_dollar(returns: pd.Series, portfolio_value: float, confidence: float = 0.95) -> float:
    """VaR in dollar terms."""
    return var_historical(returns, confidence) * portfolio_value


def cvar_dollar(returns: pd.Series, portfolio_value: float, confidence: float = 0.95) -> float:
    """CVaR in dollar terms."""
    return cvar(returns, confidence) * portfolio_value


# ── Portfolio Beta ────────────────────────────────────────────────────────────

def portfolio_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int | None = None,
) -> float:
    """
    Portfolio beta vs benchmark (SPY for US, NIFTY for India).
    beta = 1.0 → moves with market
    beta > 1.0 → amplifies market moves (aggressive)
    beta < 0   → inverse correlation (hedge instruments like SH)
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 1.0
    # Align series
    combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if len(combined) < 5:
        return 1.0
    if window:
        combined = combined.tail(window)
        if len(combined) < 5:
            return 1.0
    p = combined.iloc[:, 0]
    b = combined.iloc[:, 1]
    cov_matrix = np.cov(p, b)
    bench_var = cov_matrix[1, 1]
    if np.isnan(bench_var) or bench_var <= 1e-12:
        return 1.0
    return float(cov_matrix[0, 1] / bench_var)


def rolling_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int = 60,
) -> pd.Series:
    """Rolling beta over a sliding window."""
    betas = []
    combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    combined.columns = ["port", "bench"]
    for i in range(window, len(combined) + 1):
        slice_ = combined.iloc[i - window:i]
        cov = np.cov(slice_["port"], slice_["bench"])
        bench_var = cov[1, 1]
        beta = 1.0 if (np.isnan(bench_var) or bench_var <= 1e-12) else float(cov[0, 1] / bench_var)
        betas.append(beta)
    idx = combined.index[window - 1:]
    return pd.Series(betas, index=idx)


# ── Composite Risk Score ──────────────────────────────────────────────────────

def composite_risk_score(
    beta:        float,
    var_pct:     float,   # as decimal, e.g. -0.025
    max_dd:      float,   # as decimal, e.g. -0.12
    volatility:  float,   # annualized, e.g. 0.18
    concentration: float, # largest single position weight, e.g. 0.25
) -> int:
    """
    Composite risk score 0–100.
    0 = no risk, 100 = extreme risk.
    Used for the dashboard Risk Score gauge.

    Weights:
      Beta:          25%
      VaR:           25%
      Max Drawdown:  20%
      Volatility:    15%
      Concentration: 15%
    """
    # Normalize each factor to 0–1 scale
    beta_score    = min(1.0, max(0.0, (abs(beta) - 0.3) / 1.7))          # 0.3=low, 2.0=extreme
    var_score     = min(1.0, abs(var_pct) / 0.05)                         # 5% VaR = max
    dd_score      = min(1.0, abs(max_dd) / 0.25)                          # 25% drawdown = max
    vol_score     = min(1.0, volatility / 0.40)                           # 40% annualized = max
    conc_score    = min(1.0, max(0.0, (concentration - 0.10) / 0.40))     # 10% = ok, 50% = max

    weighted = (
        beta_score    * 0.25 +
        var_score     * 0.25 +
        dd_score      * 0.20 +
        vol_score     * 0.15 +
        conc_score    * 0.15
    )
    return round(weighted * 100)


# ── Full Metrics Bundle ───────────────────────────────────────────────────────

def compute_all_metrics(
    portfolio_returns:  pd.Series,
    benchmark_returns:  pd.Series,
    portfolio_value:    float,
    largest_position_weight: float = 0.0,
    risk_free:          float = 0.045,
) -> dict:
    """
    Compute the complete risk metrics bundle.
    Used by the daily Celery snapshot task and the /risk/metrics API endpoint.
    """
    if portfolio_returns.empty:
        return _empty_metrics()

    ret = portfolio_returns.dropna()
    bench = benchmark_returns.dropna()

    beta     = portfolio_beta(ret, bench)
    var_pct  = var_historical(ret, 0.95)
    cvar_pct = cvar(ret, 0.95)
    mdd      = max_drawdown(ret)
    sharpe   = sharpe_ratio(ret, risk_free)
    sortino  = sortino_ratio(ret, risk_free)
    calmar   = calmar_ratio(ret)
    ann_ret  = annualized_return(ret)
    ann_vol  = annualized_volatility(ret)
    wr       = win_rate(ret)

    risk_score = composite_risk_score(
        beta=beta,
        var_pct=var_pct,
        max_dd=mdd,
        volatility=ann_vol,
        concentration=largest_position_weight,
    )

    dollar_var = var_dollar(ret, portfolio_value)
    dollar_cvar = cvar_dollar(ret, portfolio_value)

    res = {
        # Core ratios
        "sharpe_ratio":           sharpe,
        "sortino_ratio":          sortino,
        "calmar_ratio":           calmar,
        # Return / vol
        "annualized_return":      ann_ret,
        "annualized_volatility":  ann_vol,
        "win_rate":               wr,
        # Risk
        "portfolio_beta":         beta,
        "max_drawdown":           mdd,
        "var_95_pct":             var_pct,
        "cvar_95_pct":            cvar_pct,
        "var_95_dollar":          dollar_var,
        "cvar_95_dollar":         dollar_cvar,
        # Composite score
        "risk_score":             risk_score,
        # Meta
        "data_points":            len(ret),
    }

    sanitized = {}
    for k, v in res.items():
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                sanitized[k] = 0.0
            elif k in ("var_95_dollar", "cvar_95_dollar"):
                sanitized[k] = round(v, 2)
            else:
                sanitized[k] = round(v, 4)
        else:
            sanitized[k] = v

    return sanitized


def _empty_metrics() -> dict:
    return {
        "sharpe_ratio": 0.0, "sortino_ratio": 0.0, "calmar_ratio": 0.0,
        "annualized_return": 0.0, "annualized_volatility": 0.0, "win_rate": 0.0,
        "portfolio_beta": 1.0, "max_drawdown": 0.0,
        "var_95_pct": 0.0, "cvar_95_pct": 0.0,
        "var_95_dollar": 0.0, "cvar_95_dollar": 0.0,
        "risk_score": 0, "data_points": 0,
    }

