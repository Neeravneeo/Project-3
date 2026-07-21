"""
Unit Test Suite for Portfolio Risk Metrics Engine (backend/app/domains/risk/metrics.py)

Fully offline, deterministic, comprehensive test suite satisfying:
- R1: Full test coverage for Sharpe, Sortino, Calmar, Max Drawdown, Beta (and rolling beta),
      VaR 95% historical (and dollar VaR), CVaR 95% historical (and dollar CVaR), Composite Risk Score,
      Parametric VaR, Win Rate, Annualized Return, Annualized Volatility, and compute_all_metrics.
- R2: Robust synthetic data generation via pytest fixtures (random walk normal & log-normal).
      Parameter variations yield non-NaN / non-Inf valid outputs.
- R3: Critical edge cases (flat/zero vol, single-day, NaN/None/Inf, empty series, mismatched lengths).
- R4: Complete offline isolation (pure unit tests, zero DB/network calls).
"""

import json
import math
import numpy as np
import pandas as pd
import pytest

from app.domains.risk.metrics import (
    _empty_metrics,
    annualized_return,
    annualized_volatility,
    calmar_ratio,
    composite_risk_score,
    compute_all_metrics,
    cvar,
    cvar_dollar,
    max_drawdown,
    portfolio_beta,
    rolling_beta,
    sharpe_ratio,
    sortino_ratio,
    var_dollar,
    var_historical,
    var_parametric,
    win_rate,
)


# ── Fixtures & Synthetic Data ───────────────────────────────────────────────────

@pytest.fixture
def seeded_random():
    """Ensure reproducibility for random return generation."""
    np.random.seed(42)


@pytest.fixture
def normal_returns(seeded_random):
    """
    252 business days of realistic daily returns.
    Mean daily ~0.05%, daily std ~1.5% (~12% annual ret, ~24% annual vol).
    """
    dates = pd.date_range("2025-01-01", periods=252, freq="B")
    data = np.random.normal(loc=0.0005, scale=0.015, size=252)
    return pd.Series(data, index=dates, name="returns")


@pytest.fixture
def lognormal_returns(seeded_random):
    """
    252 business days of log-normal returns derived from geometric Brownian motion prices.
    """
    dates = pd.date_range("2025-01-01", periods=253, freq="B")
    price_paths = 100.0 * np.exp(np.cumsum(np.random.normal(0.0003, 0.01, size=253)))
    log_rets = np.diff(np.log(price_paths))
    return pd.Series(log_rets, index=dates[1:], name="log_returns")


@pytest.fixture
def benchmark_returns(seeded_random):
    """
    252 business days benchmark returns correlated with portfolio.
    """
    dates = pd.date_range("2025-01-01", periods=252, freq="B")
    data = np.random.normal(loc=0.0004, scale=0.012, size=252)
    return pd.Series(data, index=dates, name="benchmark")


@pytest.fixture
def flat_returns():
    """100 days of zero returns (zero volatility)."""
    dates = pd.date_range("2025-01-01", periods=100, freq="B")
    return pd.Series([0.0] * 100, index=dates, name="flat")


@pytest.fixture
def single_day_returns():
    """Single day return series."""
    return pd.Series([0.015], index=pd.date_range("2025-01-01", periods=1), name="single_day")


@pytest.fixture
def empty_returns():
    """Empty return series."""
    return pd.Series([], dtype=float)


@pytest.fixture
def dirty_returns():
    """Series containing NaN and None missing values."""
    dates = pd.date_range("2025-01-01", periods=5, freq="B")
    return pd.Series([0.01, np.nan, -0.02, None, -0.005], index=dates, name="dirty")


@pytest.fixture
def unaligned_benchmark_returns(seeded_random):
    """150 business days benchmark starting at a different date offset."""
    dates = pd.date_range("2025-03-01", periods=150, freq="B")
    data = np.random.normal(loc=0.0003, scale=0.010, size=150)
    return pd.Series(data, index=dates, name="unaligned_bench")


# ── R1 Test Suite: Core Ratios & Return Metrics ───────────────────────────────

class TestSharpeRatio:
    def test_sharpe_ratio_normal_returns(self, normal_returns):
        val = sharpe_ratio(normal_returns)
        assert isinstance(val, float)
        assert not math.isnan(val)
        assert not math.isinf(val)

    def test_sharpe_ratio_zero_excess(self):
        # Daily return equal to risk_free / 252 -> excess mean = 0
        rf = 0.045
        daily_rf = rf / 252
        returns = pd.Series([daily_rf + 0.01, daily_rf - 0.01, daily_rf + 0.02, daily_rf - 0.02])
        val = sharpe_ratio(returns, risk_free=rf, periods=252)
        assert pytest.approx(val, abs=1e-6) == 0.0

    def test_sharpe_ratio_negative_returns(self):
        returns = pd.Series([-0.01, -0.02, -0.015, -0.005])
        val = sharpe_ratio(returns)
        assert val < 0.0

    def test_sharpe_ratio_flat_returns(self, flat_returns):
        # Zero volatility return series -> return 0.0
        assert sharpe_ratio(flat_returns) == 0.0

    def test_sharpe_ratio_empty_returns(self, empty_returns):
        assert sharpe_ratio(empty_returns) == 0.0

    def test_sharpe_ratio_custom_parameters(self, normal_returns):
        val_weekly = sharpe_ratio(normal_returns, risk_free=0.065, periods=52)
        val_monthly = sharpe_ratio(normal_returns, risk_free=0.02, periods=12)
        assert isinstance(val_weekly, float)
        assert isinstance(val_monthly, float)

    def test_sharpe_ratio_single_element(self, single_day_returns):
        val = sharpe_ratio(single_day_returns)
        assert val == 0.0


class TestSortinoRatio:
    def test_sortino_ratio_normal_returns(self, normal_returns):
        val = sortino_ratio(normal_returns)
        assert isinstance(val, float)
        assert not math.isnan(val)

    def test_sortino_ratio_no_downside_returns(self):
        # Only positive returns -> downside is empty -> float("inf")
        returns = pd.Series([0.01, 0.02, 0.015, 0.005])
        val = sortino_ratio(returns)
        assert val == float("inf")

    def test_sortino_ratio_all_negative_returns(self):
        returns = pd.Series([-0.01, -0.02, -0.015, -0.005])
        val = sortino_ratio(returns)
        assert isinstance(val, float)
        assert val < 0.0

    def test_sortino_ratio_flat_returns(self, flat_returns):
        assert sortino_ratio(flat_returns) == 0.0

    def test_sortino_ratio_empty_returns(self, empty_returns):
        assert sortino_ratio(empty_returns) == 0.0

    def test_sortino_ratio_custom_parameters(self, normal_returns):
        val = sortino_ratio(normal_returns, risk_free=0.05, periods=52)
        assert isinstance(val, float)

    def test_sortino_ratio_near_zero_downside_std(self):
        val = sortino_ratio(pd.Series([-1e-14, -1e-14]))
        assert val == 0.0


class TestMaxDrawdown:
    def test_max_drawdown_known_sequence(self):
        # Known price sequence: 100 -> 120 (+20%) -> 90 (-25%) -> 105 (+16.67%)
        # Returns: [+0.20, -0.25, 15.0 / 90.0]
        returns = pd.Series([0.20, -0.25, 15.0 / 90.0])
        # Peak cumprod is 1.20, trough is 0.90 -> DD = (0.90 - 1.20) / 1.20 = -0.25
        mdd = max_drawdown(returns)
        assert pytest.approx(mdd, rel=1e-4) == -0.25

    def test_max_drawdown_strictly_increasing(self):
        returns = pd.Series([0.01, 0.02, 0.03, 0.01])
        assert max_drawdown(returns) == 0.0

    def test_max_drawdown_strictly_decreasing(self):
        returns = pd.Series([-0.10, -0.10, -0.10])
        # cumprod: [0.9, 0.81, 0.729], cummax peak: [0.9, 0.9, 0.9]
        # drawdown from first price: (0.729 - 0.9) / 0.9 = -0.19
        mdd = max_drawdown(returns)
        assert pytest.approx(mdd, rel=1e-4) == -0.19

    def test_max_drawdown_flat_returns(self, flat_returns):
        assert max_drawdown(flat_returns) == 0.0

    def test_max_drawdown_empty_returns(self, empty_returns):
        assert max_drawdown(empty_returns) == 0.0


class TestCalmarRatio:
    def test_calmar_ratio_normal_returns(self, normal_returns):
        calmar = calmar_ratio(normal_returns)
        assert isinstance(calmar, float)
        assert not math.isnan(calmar)

    def test_calmar_ratio_zero_drawdown(self):
        # Strictly positive returns have mdd = 0.0 -> returns float("inf")
        returns = pd.Series([0.01, 0.02, 0.015])
        assert calmar_ratio(returns) == float("inf")

    def test_calmar_ratio_flat_returns(self, flat_returns):
        assert calmar_ratio(flat_returns) == 0.0

    def test_calmar_ratio_empty_returns(self, empty_returns):
        assert calmar_ratio(empty_returns) == 0.0

    def test_calmar_ratio_custom_periods(self, normal_returns):
        val = calmar_ratio(normal_returns, periods=52)
        assert isinstance(val, float)


class TestAnnualizedMetrics:
    def test_annualized_return_calculation(self):
        # Mean return 0.001 per day over 252 days: (1 + 0.001)^252 - 1 ≈ 0.2863
        returns = pd.Series([0.001] * 252)
        ann_ret = annualized_return(returns, periods=252)
        expected = (1.001 ** 252) - 1.0
        assert pytest.approx(ann_ret, rel=1e-5) == expected

    def test_annualized_return_empty(self, empty_returns):
        assert annualized_return(empty_returns) == 0.0

    def test_annualized_volatility_calculation(self, normal_returns):
        vol = annualized_volatility(normal_returns)
        assert isinstance(vol, float)
        assert vol > 0.0

    def test_annualized_volatility_flat(self, flat_returns):
        assert annualized_volatility(flat_returns) == 0.0

    def test_annualized_volatility_empty(self, empty_returns):
        assert annualized_volatility(empty_returns) == 0.0


class TestWinRate:
    def test_win_rate_mixed(self):
        # 3 positive out of 5 returns -> 0.60
        returns = pd.Series([0.01, -0.005, 0.02, 0.0, -0.01])
        # > 0 count is 2 (0.01, 0.02) out of 5 -> 0.40
        assert win_rate(returns) == 0.40

    def test_win_rate_all_positive(self):
        returns = pd.Series([0.01, 0.02, 0.005])
        assert win_rate(returns) == 1.0

    def test_win_rate_all_negative(self):
        returns = pd.Series([-0.01, -0.02, -0.005])
        assert win_rate(returns) == 0.0

    def test_win_rate_empty(self, empty_returns):
        assert win_rate(empty_returns) == 0.0


# ── R1 Test Suite: Value at Risk & CVaR ───────────────────────────────────────

class TestValueAtRisk:
    def test_var_historical_normal_returns(self, normal_returns):
        var_95 = var_historical(normal_returns, confidence=0.95)
        var_99 = var_historical(normal_returns, confidence=0.99)
        assert isinstance(var_95, float)
        assert var_95 < 0.0  # Loss representation
        assert var_99 <= var_95  # 99% VaR is a worse loss than 95% VaR

    def test_var_historical_empty(self, empty_returns):
        assert var_historical(empty_returns) == 0.0

    def test_var_parametric(self, normal_returns):
        pvar = var_parametric(normal_returns, confidence=0.95)
        assert isinstance(pvar, float)
        assert pvar < 0.0

    def test_var_parametric_empty(self, empty_returns):
        assert var_parametric(empty_returns) == 0.0

    def test_var_parametric_zero_variance(self):
        val = var_parametric(pd.Series([0.01] * 100))
        assert val == 0.0

    def test_var_dollar_scaling(self, normal_returns):
        var_pct = var_historical(normal_returns, 0.95)
        portfolio_val = 250000.0
        dollar_var = var_dollar(normal_returns, portfolio_value=portfolio_val, confidence=0.95)
        assert pytest.approx(dollar_var) == var_pct * portfolio_val


class TestConditionalValueAtRisk:
    def test_cvar_historical_normal_returns(self, normal_returns):
        var_95 = var_historical(normal_returns, confidence=0.95)
        cvar_95 = cvar(normal_returns, confidence=0.95)
        assert isinstance(cvar_95, float)
        # CVaR is expected loss in tail <= VaR, so cvar_95 <= var_95 (more negative)
        assert cvar_95 <= var_95

    def test_cvar_empty(self, empty_returns):
        assert cvar(empty_returns) == 0.0

    def test_cvar_dollar_scaling(self, normal_returns):
        cvar_pct = cvar(normal_returns, 0.95)
        portfolio_val = 500000.0
        dollar_cvar = cvar_dollar(normal_returns, portfolio_value=portfolio_val, confidence=0.95)
        assert pytest.approx(dollar_cvar) == cvar_pct * portfolio_val


# ── R1 Test Suite: Portfolio Beta & Rolling Beta ───────────────────────────────

class TestPortfolioBeta:
    def test_beta_identical_series(self, normal_returns):
        beta = portfolio_beta(normal_returns, normal_returns)
        assert pytest.approx(beta, rel=1e-4) == 1.0

    def test_beta_inverse_series(self, normal_returns):
        beta = portfolio_beta(normal_returns, -normal_returns)
        assert pytest.approx(beta, rel=1e-4) == -1.0

    def test_beta_amplified_series(self, normal_returns):
        beta = portfolio_beta(2.0 * normal_returns, normal_returns)
        assert pytest.approx(beta, rel=1e-4) == 2.0

    def test_beta_zero_benchmark_variance(self, normal_returns, flat_returns):
        beta = portfolio_beta(normal_returns, flat_returns)
        assert beta == 1.0

    def test_beta_short_series(self):
        # Less than 5 matching rows defaults to 1.0
        port = pd.Series([0.01, 0.02, -0.01, 0.005])
        bench = pd.Series([0.005, 0.01, -0.005, 0.002])
        assert portfolio_beta(port, bench) == 1.0

    def test_beta_empty_returns(self, empty_returns, normal_returns):
        assert portfolio_beta(empty_returns, normal_returns) == 1.0
        assert portfolio_beta(normal_returns, empty_returns) == 1.0
        assert portfolio_beta(empty_returns, empty_returns) == 1.0

    def test_beta_mismatched_lengths_and_unaligned_dates(self, normal_returns, unaligned_benchmark_returns):
        # normal_returns has 252 days from Jan 1, unaligned_benchmark_returns has 150 days from Mar 1
        beta = portfolio_beta(normal_returns, unaligned_benchmark_returns)
        assert isinstance(beta, float)
        assert not math.isnan(beta)

    def test_beta_window_parameter(self, normal_returns, benchmark_returns):
        beta_full = portfolio_beta(normal_returns, benchmark_returns)
        beta_window = portfolio_beta(normal_returns, benchmark_returns, window=30)
        assert isinstance(beta_full, float)
        assert isinstance(beta_window, float)

    def test_portfolio_beta_small_window(self, normal_returns, benchmark_returns):
        val = portfolio_beta(normal_returns, benchmark_returns, window=3)
        assert val == 1.0


class TestRollingBeta:
    def test_rolling_beta_structure(self, normal_returns, benchmark_returns):
        r_beta = rolling_beta(normal_returns, benchmark_returns, window=60)
        assert isinstance(r_beta, pd.Series)
        expected_len = len(normal_returns) - 60 + 1
        assert len(r_beta) == expected_len
        assert not r_beta.isna().any()

    def test_rolling_beta_identical_series(self, normal_returns):
        r_beta = rolling_beta(normal_returns, normal_returns, window=30)
        assert (r_beta == 1.0).all()

    def test_rolling_beta_zero_variance_slice(self, normal_returns, flat_returns):
        r_beta = rolling_beta(normal_returns, flat_returns, window=30)
        assert (r_beta == 1.0).all()

    def test_rolling_beta_insufficient_length(self):
        dates = pd.date_range("2025-01-01", periods=10)
        port = pd.Series(np.random.normal(0, 0.01, 10), index=dates)
        bench = pd.Series(np.random.normal(0, 0.01, 10), index=dates)
        r_beta = rolling_beta(port, bench, window=60)
        assert r_beta.empty


# ── R1 Test Suite: Composite Risk Score ───────────────────────────────────────

class TestCompositeRiskScore:
    def test_composite_risk_score_bounds(self):
        score_low = composite_risk_score(beta=0.5, var_pct=-0.01, max_dd=-0.05, volatility=0.10, concentration=0.10)
        score_high = composite_risk_score(beta=2.5, var_pct=-0.10, max_dd=-0.40, volatility=0.50, concentration=0.60)
        assert 0 <= score_low <= 100
        assert 0 <= score_high <= 100
        assert score_low < score_high

    def test_composite_risk_score_clamping_extreme_inputs(self):
        score_max = composite_risk_score(beta=10.0, var_pct=-0.50, max_dd=-0.90, volatility=2.0, concentration=1.0)
        assert score_max == 100

        score_min = composite_risk_score(beta=0.0, var_pct=0.0, max_dd=0.0, volatility=0.0, concentration=0.0)
        assert score_min == 0

    def test_composite_risk_score_monotonicity(self):
        base_score = composite_risk_score(beta=1.0, var_pct=-0.02, max_dd=-0.10, volatility=0.15, concentration=0.15)
        higher_beta_score = composite_risk_score(beta=1.8, var_pct=-0.02, max_dd=-0.10, volatility=0.15, concentration=0.15)
        higher_dd_score = composite_risk_score(beta=1.0, var_pct=-0.02, max_dd=-0.25, volatility=0.15, concentration=0.15)

        assert higher_beta_score > base_score
        assert higher_dd_score > base_score


# ── R1 & R2 Test Suite: Compute All Metrics & Synthetic Distributions ─────────

class TestComputeAllMetrics:
    def test_compute_all_metrics_normal(self, normal_returns, benchmark_returns):
        metrics = compute_all_metrics(
            portfolio_returns=normal_returns,
            benchmark_returns=benchmark_returns,
            portfolio_value=100000.0,
            largest_position_weight=0.25,
            risk_free=0.045,
        )
        assert isinstance(metrics, dict)
        expected_keys = {
            "sharpe_ratio", "sortino_ratio", "calmar_ratio",
            "annualized_return", "annualized_volatility", "win_rate",
            "portfolio_beta", "max_drawdown", "var_95_pct", "cvar_95_pct",
            "var_95_dollar", "cvar_95_dollar", "risk_score", "data_points"
        }
        assert set(metrics.keys()) == expected_keys
        assert metrics["data_points"] == 252
        assert 0 <= metrics["risk_score"] <= 100

    def test_compute_all_metrics_empty(self, empty_returns, benchmark_returns):
        metrics = compute_all_metrics(
            portfolio_returns=empty_returns,
            benchmark_returns=benchmark_returns,
            portfolio_value=100000.0,
        )
        assert metrics == _empty_metrics()

    def test_compute_all_metrics_dirty_returns(self, dirty_returns, benchmark_returns):
        # dirty_returns has NaN and None missing values
        metrics = compute_all_metrics(
            portfolio_returns=dirty_returns,
            benchmark_returns=benchmark_returns,
            portfolio_value=100000.0,
        )
        assert isinstance(metrics, dict)
        assert metrics["data_points"] == 3  # 5 minus 2 missing (NaN, None) = 3
        assert not math.isnan(metrics["sharpe_ratio"])

    def test_compute_all_metrics_lognormal(self, lognormal_returns, benchmark_returns):
        metrics = compute_all_metrics(
            portfolio_returns=lognormal_returns,
            benchmark_returns=benchmark_returns,
            portfolio_value=500000.0,
            largest_position_weight=0.15,
        )
        assert isinstance(metrics, dict)
        assert metrics["data_points"] == 252

    def test_compute_all_metrics_sanitizes_infinity(self):
        metrics = compute_all_metrics(pd.Series([0.05] * 10), pd.Series([0.02] * 10), 100000.0)
        assert isinstance(metrics, dict)
        assert metrics["sortino_ratio"] == 0.0


class TestParameterVariationsAndOutputValidity:
    """R2: Verify parameter variations yield valid non-NaN / non-Inf metrics."""

    @pytest.mark.parametrize("seed", [1, 42, 100, 999])
    def test_random_seed_variations(self, seed):
        np.random.seed(seed)
        port = pd.Series(np.random.normal(0.0002, 0.02, 200))
        bench = pd.Series(np.random.normal(0.0001, 0.015, 200))
        metrics = compute_all_metrics(port, bench, portfolio_value=100000.0)

        for key, val in metrics.items():
            if isinstance(val, float):
                assert not math.isnan(val), f"Key {key} is NaN for seed {seed}"
                assert not math.isinf(val), f"Key {key} is Inf for seed {seed}"


# ── R3 & R4 Edge Cases & Offline Isolation Test Suite ─────────────────────────

class TestCriticalEdgeCases:
    """R3: Comprehensive suite testing all mandated critical edge cases."""

    def test_flat_zero_volatility_return_series(self, flat_returns, benchmark_returns):
        assert sharpe_ratio(flat_returns) == 0.0
        assert sortino_ratio(flat_returns) == 0.0
        assert max_drawdown(flat_returns) == 0.0
        assert calmar_ratio(flat_returns) == 0.0
        assert annualized_volatility(flat_returns) == 0.0
        assert portfolio_beta(flat_returns, benchmark_returns) == 0.0

    def test_single_day_return_series(self, single_day_returns, benchmark_returns):
        # Beta requires >= 5 rows, defaults to 1.0
        assert portfolio_beta(single_day_returns, benchmark_returns) == 1.0
        assert win_rate(single_day_returns) == 1.0
        assert max_drawdown(single_day_returns) == 0.0

    def test_extreme_float_values_inf_max_min(self, benchmark_returns):
        """Verify extreme float inputs (inf, -inf, 1e308, 1e-308) return sanitized non-NaN/non-Inf dict."""
        for extreme_val in [np.inf, -np.inf, 1e308, 1e-308]:
            s = pd.Series([extreme_val, 0.01, -0.02])
            metrics = compute_all_metrics(s, benchmark_returns, portfolio_value=100000.0)
            assert isinstance(metrics, dict)
            for k, v in metrics.items():
                if isinstance(v, float):
                    assert not math.isnan(v), f"Metric {k} was NaN for input {extreme_val}"
                    assert not math.isinf(v), f"Metric {k} was Inf for input {extreme_val}"

    def test_all_nan_series_safe_handling(self, benchmark_returns):
        """Verify series with all NaN or all None values handles safely without throwing exceptions."""
        all_nan = pd.Series([np.nan, np.nan, np.nan])
        metrics = compute_all_metrics(all_nan, benchmark_returns, portfolio_value=100000.0)
        assert metrics["data_points"] == 0
        assert metrics["sharpe_ratio"] == 0.0
        assert metrics["max_drawdown"] == 0.0

        all_none = pd.Series([None, None, None])
        metrics_none = compute_all_metrics(all_none, benchmark_returns, portfolio_value=100000.0)
        assert metrics_none["data_points"] == 0
        assert metrics_none["sharpe_ratio"] == 0.0
        assert metrics_none["max_drawdown"] == 0.0



class TestRemediatedEdgeCases:
    """Test cases mandated for Challenger 1 risk metrics remediation."""

    def test_constant_return_series_float_noise(self):
        rets = pd.Series([0.01] * 100)
        assert sharpe_ratio(rets) == 0.0

    def test_single_element_series_metrics(self):
        s = pd.Series([0.01])
        assert sharpe_ratio(s) == 0.0
        assert annualized_volatility(s) == 0.0
        assert var_parametric(s) == 0.0

    def test_constant_loss_series_sortino(self):
        rets = pd.Series([-0.01] * 100)
        val = sortino_ratio(rets)
        assert val <= 0.0
        assert not math.isinf(val)

    def test_constant_benchmark_series_beta(self, normal_returns):
        bench = pd.Series([0.01] * len(normal_returns), index=normal_returns.index)
        assert portfolio_beta(normal_returns, bench) == 1.0

    def test_day_zero_wipeout_max_drawdown(self):
        rets = pd.Series([-1.0, 0.05])
        assert max_drawdown(rets) == -1.0

    def test_clean_json_serialization(self, normal_returns, benchmark_returns):
        metrics = compute_all_metrics(normal_returns, benchmark_returns, portfolio_value=100000.0)
        json_str = json.dumps(metrics)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["sharpe_ratio"] == metrics["sharpe_ratio"]


class TestOfflineIsolation:
    """R4: Complete offline isolation check."""

    def test_no_external_network_or_db_dependencies(self, normal_returns, benchmark_returns, monkeypatch):
        # Explicitly guard socket connect to prove offline execution
        import socket
        def guard_connect(*args, **kwargs):
            raise RuntimeError("Network socket connect attempted!")
        monkeypatch.setattr(socket.socket, "connect", guard_connect)

        metrics = compute_all_metrics(normal_returns, benchmark_returns, portfolio_value=100000.0)
        assert metrics["data_points"] == 252


