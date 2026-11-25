"""Deterministic tests for Appendix D.6 Breaking Point (Reverse Stress Testing)."""

import numpy as np
import pytest

from risk_core.breaking_point import solve_breaking_point


def test_fixture_d6_breaking_point():
    """D.6 Breaking Point:
    Exposures b = (0.80, 0.60); monthly vol = (5%, 2.5%); corr = -0.30 ->
    C = [[0.0025, -0.000375], [-0.000375, 0.000625]]; a = -b; a^T * C * a = 0.001465; T = 0.15.

    Solutions:
    - Unconstrained: equity -18.174%, USD -0.768%, distance 3.919, Gaussian tail 4.45e-5
    - Equity-only: equity -18.750%, distance 3.931
    - Equity >= -10%: equity -10.000%, USD -11.667%, distance 5.872
    Each solution has loss exactly 15.0%.
    """
    factor_names = ["EQUITY", "USD"]
    b = np.array([0.80, 0.60])
    c_mat = np.array([
        [0.0025, -0.000375],
        [-0.000375, 0.000625],
    ])
    threshold = 0.15

    solutions = solve_breaking_point(
        factor_names=factor_names,
        factor_exposures=b,
        factor_cov=c_mat,
        loss_threshold=threshold,
        cap_first_factor=-0.10,
    )

    # 1. Unconstrained
    sol_unconstrained = solutions["unconstrained"]
    assert pytest.approx(sol_unconstrained.shocks["EQUITY"], abs=1e-4) == -0.18174
    assert pytest.approx(sol_unconstrained.shocks["USD"], abs=1e-4) == -0.00768
    assert pytest.approx(sol_unconstrained.mahalanobis_distance, abs=1e-3) == 3.919
    assert pytest.approx(sol_unconstrained.gaussian_tail_probability, rel=1e-2) == 4.45e-5
    assert pytest.approx(sol_unconstrained.loss, rel=1e-9) == 0.150

    # 2. Equity-only
    sol_eq = solutions["equity_only"]
    assert pytest.approx(sol_eq.shocks["EQUITY"], abs=1e-4) == -0.18750
    assert pytest.approx(sol_eq.shocks["USD"], abs=1e-6) == 0.0
    assert pytest.approx(sol_eq.mahalanobis_distance, abs=1e-3) == 3.931
    assert pytest.approx(sol_eq.loss, rel=1e-9) == 0.150

    # 3. Equity capped at -10%
    sol_capped = solutions["equity_capped"]
    assert pytest.approx(sol_capped.shocks["EQUITY"], abs=1e-4) == -0.10000
    assert pytest.approx(sol_capped.shocks["USD"], abs=1e-4) == -0.11667
    assert pytest.approx(sol_capped.mahalanobis_distance, abs=1e-3) == 5.872
    assert pytest.approx(sol_capped.loss, rel=1e-9) == 0.150
