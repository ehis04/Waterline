"""Hypothesis property-based tests for risk_core invariants."""

from hypothesis import given, settings, strategies as st
import numpy as np
import pytest

from risk_core.euler import calculate_euler_contributions
from risk_core.metrics import calculate_hhi, calculate_historical_var_es


@settings(max_examples=50)
@given(
    st.lists(st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False), min_size=20, max_size=200),
    st.floats(min_value=0.90, max_value=0.99),
)
def test_var_es_monotonicity_property(raw_losses, alpha):
    """Property: For any distribution of losses, Expected Shortfall is always >= Value at Risk."""
    res = calculate_historical_var_es(raw_losses, alpha=alpha)
    if res.is_ok:
        var, es = res.value
        assert es >= var - 1e-9


@settings(max_examples=50)
@given(
    st.lists(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=20)
)
def test_hhi_bounds_property(weights):
    """Property: HHI is bounded in [1/N, 1.0], and N_eff is bounded in [1.0, N]."""
    hhi, n_eff = calculate_hhi(weights)
    n = len(weights)
    assert hhi <= 1.0 + 1e-9
    assert hhi >= (1.0 / n) - 1e-9
    assert n_eff >= 1.0 - 1e-9
    assert n_eff <= n + 1e-9


@settings(max_examples=50)
@given(
    st.floats(min_value=0.05, max_value=0.5),
    st.floats(min_value=0.05, max_value=0.5),
    st.floats(min_value=-0.8, max_value=0.8),
    st.floats(min_value=0.01, max_value=0.99),
)
def test_euler_sum_identity_property(vol1, vol2, corr, w1):
    """Property: Sum of component risk contributions equals total portfolio volatility."""
    w = np.array([w1, 1.0 - w1])
    cov = np.array([
        [vol1 ** 2, corr * vol1 * vol2],
        [corr * vol1 * vol2, vol2 ** 2],
    ])
    sigma_p, mrc, rc = calculate_euler_contributions(w, cov)
    assert pytest.approx(np.sum(rc), rel=1e-7) == sigma_p
