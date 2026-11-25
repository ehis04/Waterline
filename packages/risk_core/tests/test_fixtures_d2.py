"""Deterministic tests for Appendix D.2 VaR and Expected Shortfall conventions."""

import pytest
from risk_core.metrics import calculate_historical_var_es


def test_fixture_d2_var_es_convention():
    """D.2 VaR/ES convention:
    100 daily losses; the five largest are 5.0%, 4.2%, 3.6%, 3.1%, 2.9%; the 95th smallest is 2.5%.
    With alpha = 0.95, k = 95: VaR = 2.5%; ES = (5.0 + 4.2 + 3.6 + 3.1 + 2.9)/5 = 3.76%.
    ES >= VaR holds.
    """
    # 94 smaller losses ranging from 0.1% to 2.4%
    smaller_losses = [0.001 + (i * 0.023 / 93) for i in range(94)]
    # 95th smallest is 2.5%
    var_point = 0.025
    # The five largest tail losses
    tail = [0.029, 0.031, 0.036, 0.042, 0.050]

    all_losses = smaller_losses + [var_point] + tail
    assert len(all_losses) == 100

    res = calculate_historical_var_es(all_losses, alpha=0.95)
    assert res.is_ok
    var_est, es_est = res.value

    assert pytest.approx(var_est, rel=1e-5) == 0.025
    assert pytest.approx(es_est, rel=1e-5) == 0.0376
    assert es_est >= var_est
