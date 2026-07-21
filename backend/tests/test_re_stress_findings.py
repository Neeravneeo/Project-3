"""
Empirical Re-Stress Testing for Risk Metrics Engine (Iteration 2 Verification)
Target: backend/app/domains/risk/metrics.py

This test suite specifically probes the 7 numerical instability findings from Iteration 1:
1. Constant return series float noise (`sharpe_ratio([0.01]*100)`)
2. Single-element series (N=1) NaN leak
3. Constant loss series Sortino ratio
4. Constant benchmark series Beta float noise
5. Day 0 portfolio wipeout (-100% return) Max Drawdown
6. Clean JSON payload serialization
7. Random seed variations
"""

import json
import math
import numpy as np
import pandas as pd
import pytest

from app.domains.risk.metrics import (
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


class TestFinding1ConstantReturnSeriesFloatNoise:
    """Finding 1: Constant return series floating point noise standard deviation."""

    def test_sharpe_ratio_constant_positive(self):
        rets = pd.Series([0.01] * 100)
        # std of [0.01]*100 is ~1.73e-18 in IEEE 754 float
        val = sharpe_ratio(rets)
        assert val == 0.0, f"Expected 0.0, got {val}"

    def test_sharpe_ratio_constant_negative(self):
        rets = pd.Series([-0.005] * 500)
        val = sharpe_ratio(rets)
        assert val == 0.0, f"Expected 0.0, got {val}"

    def test_sharpe_ratio_constant_zero(self):
        rets = pd.Series([0.0] * 252)
        val = sharpe_ratio(rets)
        assert val == 0.0, f"Expected 0.0, got {val}"

    def test_annualized_volatility_constant(self):
        rets = pd.Series([0.02] * 100)
        vol = annualized_volatility(rets)
        assert vol == 0.0, f"Expected 0.0, got {vol}"


class TestFinding2SingleElementSeriesNaNLeak:
    """Finding 2: Single-element series (N=1) NaN leak in std/cov calculation."""

    def test_single_element_all_metrics(self):
        s = pd.Series([0.015], index=pd.date_range("2025-01-01", periods=1))
        
        assert sharpe_ratio(s) == 0.0
        assert sortino_ratio(s) == 0.0
        assert max_drawdown(s) == 0.0
        assert calmar_ratio(s) == 0.0
        assert annualized_return(s) == float((1.015 ** 252) - 1.0)
        assert annualized_volatility(s) == 0.0
        assert win_rate(s) == 1.0
        assert var_historical(s) == 0.015
        assert var_parametric(s) == 0.0
        assert cvar(s) == 0.015
        
        bench = pd.Series([0.010], index=pd.date_range("2025-01-01", periods=1))
        assert portfolio_beta(s, bench) == 1.0

    def test_single_element_compute_all_metrics(self):
        s = pd.Series([0.05])
        bench = pd.Series([0.02])
        res = compute_all_metrics(s, bench, portfolio_value=100000.0)
        
        for k, v in res.items():
            if isinstance(v, float):
                assert not math.isnan(v), f"Metric {k} is NaN for single-element series"
                assert not math.isinf(v), f"Metric {k} is Inf for single-element series"


class TestFinding3ConstantLossSeriesSortinoRatio:
    """Finding 3: Constant loss series Sortino ratio behavior."""

    def test_constant_loss_sortino(self):
        rets = pd.Series([-0.01] * 100)
        val = sortino_ratio(rets)
        # downside RMSD is ~0.01 * sqrt(252), excess is negative -> val should be negative finite float
        assert isinstance(val, float)
        assert not math.isnan(val), "Sortino ratio returned NaN for constant loss"
        assert not math.isinf(val), "Sortino ratio returned Inf for constant loss"
        assert val < 0.0, f"Expected negative Sortino, got {val}"

    def test_all_positive_returns_sortino(self):
        rets = pd.Series([0.01] * 100)
        # All positive returns -> downside is empty -> returns inf if ann_ret > risk_free else 0.0
        val = sortino_ratio(rets)
        assert val == float("inf")
        # In compute_all_metrics, inf should be sanitized to 0.0
        metrics = compute_all_metrics(rets, rets, portfolio_value=100000.0)
        assert metrics["sortino_ratio"] == 0.0


class TestFinding4ConstantBenchmarkSeriesBetaFloatNoise:
    """Finding 4: Constant benchmark series Beta floating point noise variance."""

    def test_constant_benchmark_portfolio_beta(self):
        port = pd.Series(np.random.normal(0.001, 0.02, 100))
        bench = pd.Series([0.01] * 100)
        beta = portfolio_beta(port, bench)
        assert beta == 1.0, f"Expected Beta=1.0 for constant benchmark, got {beta}"

    def test_constant_benchmark_rolling_beta(self):
        port = pd.Series(np.random.normal(0.001, 0.02, 100))
        bench = pd.Series([0.01] * 100)
        r_beta = rolling_beta(port, bench, window=30)
        assert (r_beta == 1.0).all(), "Expected all rolling betas to be 1.0 for constant benchmark"


class TestFinding5DayZeroPortfolioWipeoutMaxDrawdown:
    """Finding 5: Day 0 portfolio wipeout (-100% return) Max Drawdown calculation."""

    def test_day_zero_wipeout_returns(self):
        rets = pd.Series([-1.0, 0.05, 0.02])
        mdd = max_drawdown(rets)
        assert mdd == -1.0, f"Expected -1.0 max drawdown for total wipeout, got {mdd}"

    def test_immediate_wipeout(self):
        rets = pd.Series([-1.0])
        mdd = max_drawdown(rets)
        assert mdd == -1.0, f"Expected -1.0 max drawdown, got {mdd}"

    def test_severe_drawdown_near_wipeout(self):
        rets = pd.Series([-0.999999999999, 0.50])
        mdd = max_drawdown(rets)
        assert mdd == -1.0 or pytest.approx(mdd, abs=1e-5) == -1.0


class TestFinding6CleanJSONPayloadSerialization:
    """Finding 6: Clean JSON payload serialization without NaN or Inf literals."""

    @pytest.mark.parametrize("scenario", [
        "flat", "single", "all_pos", "all_neg", "wipeout", "empty", "dirty"
    ])
    def test_json_serialization_edge_cases(self, scenario):
        if scenario == "flat":
            port = pd.Series([0.0] * 100)
            bench = pd.Series([0.0] * 100)
        elif scenario == "single":
            port = pd.Series([0.01])
            bench = pd.Series([0.01])
        elif scenario == "all_pos":
            port = pd.Series([0.02] * 100)
            bench = pd.Series([0.01] * 100)
        elif scenario == "all_neg":
            port = pd.Series([-0.02] * 100)
            bench = pd.Series([-0.01] * 100)
        elif scenario == "wipeout":
            port = pd.Series([-1.0, 0.05])
            bench = pd.Series([0.01, 0.01])
        elif scenario == "empty":
            port = pd.Series([])
            bench = pd.Series([])
        elif scenario == "dirty":
            port = pd.Series([0.01, np.nan, -0.02, None, np.inf])
            bench = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])

        metrics = compute_all_metrics(port, bench, portfolio_value=100000.0)
        json_str = json.dumps(metrics)
        parsed = json.loads(json_str)
        
        assert isinstance(parsed, dict)
        for k, v in parsed.items():
            if isinstance(v, float):
                assert not math.isnan(v), f"JSON value for {k} in {scenario} is NaN"
                assert not math.isinf(v), f"JSON value for {k} in {scenario} is Inf"


class TestFinding7RandomSeedVariations:
    """Finding 7: Comprehensive random seed variations across distributions & lengths."""

    @pytest.mark.parametrize("seed", list(range(1, 51)))
    def test_random_seeds_broad(self, seed):
        np.random.seed(seed)
        n = np.random.randint(5, 500)
        loc = np.random.uniform(-0.05, 0.05)
        scale = np.random.uniform(0.001, 0.10)
        
        port = pd.Series(np.random.normal(loc, scale, n))
        bench = pd.Series(np.random.normal(0.0005, 0.015, n))
        
        metrics = compute_all_metrics(port, bench, portfolio_value=np.random.uniform(1000, 1000000))
        json_str = json.dumps(metrics)
        parsed = json.loads(json_str)

        for k, v in parsed.items():
            if isinstance(v, float):
                assert not math.isnan(v), f"Seed {seed}: {k} is NaN"
                assert not math.isinf(v), f"Seed {seed}: {k} is Inf"
