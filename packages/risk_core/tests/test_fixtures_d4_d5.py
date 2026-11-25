"""Deterministic tests for Appendix D.4 Euler Contributions and D.5 Risk Diff."""

import numpy as np
import pytest

from risk_core.euler import calculate_euler_contributions, calculate_portfolio_volatility
from risk_core.risk_diff import calculate_risk_diff


def test_fixture_d4_euler_contributions():
    """D.4 Euler contributions.
    Weights (0.7, 0.3); volatilities 25% and 5%; correlation 0.4 ->
    sigma_p = 18.152%; RC = (17.450%, 0.702%); sum = sigma_p.
    """
    weights = np.array([0.7, 0.3])
    vol1 = 0.25
    vol2 = 0.05
    corr = 0.4

    cov = np.array([
        [vol1 ** 2, corr * vol1 * vol2],
        [corr * vol1 * vol2, vol2 ** 2],
    ])

    sigma_p, mrc, rc = calculate_euler_contributions(weights, cov)

    assert pytest.approx(sigma_p, abs=1e-4) == 0.18152
    assert pytest.approx(rc[0], abs=1e-4) == 0.17450
    assert pytest.approx(rc[1], abs=1e-4) == 0.00702
    assert pytest.approx(np.sum(rc), rel=1e-9) == sigma_p


def test_fixture_d5_risk_diff():
    """D.5 Risk Diff (two components; method and data unchanged).
    A: weights (0.6, 0.4), vols (15%, 5%), rho = 0.2.
    B: weights (0.7, 0.3), vols (25%, 5%), rho = 0.4.
    phi_H = 1.772 pts; phi_M = 6.778 pts; sum = 8.550 pts = total change.
    """
    weights_a = np.array([0.6, 0.4])
    cov_a = np.array([
        [0.15 ** 2, 0.2 * 0.15 * 0.05],
        [0.2 * 0.15 * 0.05, 0.05 ** 2],
    ])

    weights_b = np.array([0.7, 0.3])
    cov_b = np.array([
        [0.25 ** 2, 0.4 * 0.25 * 0.05],
        [0.4 * 0.25 * 0.05, 0.05 ** 2],
    ])

    res = calculate_risk_diff(weights_a, cov_a, weights_b, cov_b)

    assert pytest.approx(res.vol_start, abs=1e-4) == 0.09602
    assert pytest.approx(res.vol_end, abs=1e-4) == 0.18152
    assert pytest.approx(res.total_change, abs=1e-4) == 0.08550
    assert pytest.approx(res.holdings_contribution, abs=1e-4) == 0.01772
    assert pytest.approx(res.market_contribution, abs=1e-4) == 0.06778
    assert pytest.approx(res.holdings_contribution + res.market_contribution, rel=1e-9) == res.total_change
