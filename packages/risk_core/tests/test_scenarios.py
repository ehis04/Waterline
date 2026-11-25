"""Tests for hypothetical stress testing and Rule Q-31 asset overrides."""

from decimal import Decimal
import pytest

from risk_core.types import Position
from risk_core.scenarios import apply_hypothetical_shocks


def test_rule_q31_asset_overrides_replace_factor_return():
    """Rule Q-31: Direct asset overrides replace, not add to, factor-implied returns."""
    positions = [
        Position("INST_A", Decimal("100"), Decimal("100"), Decimal("100"), Decimal("10000.00"), "EUR"),
        Position("INST_B", Decimal("50"), Decimal("100"), Decimal("100"), Decimal("5000.00"), "EUR"),
    ]

    factor_shocks = {"GLOBAL_EQ": -0.20}
    # Both assets have beta 1.0 to GLOBAL_EQ
    factor_betas = {
        "INST_A": {"GLOBAL_EQ": 1.0},
        "INST_B": {"GLOBAL_EQ": 1.0},
    }

    # Direct override for INST_A to -0.35 (e.g. user specifically shocks INST_A harder)
    # INST_B should get factor-implied shock -0.20
    asset_overrides = {"INST_A": -0.35}

    res = apply_hypothetical_shocks(
        positions=positions,
        factor_shocks=factor_shocks,
        factor_betas=factor_betas,
        asset_overrides=asset_overrides,
    )

    assert res.asset_returns["INST_A"] == -0.35  # Overridden, NOT -0.20 + -0.35 = -0.55
    assert res.asset_returns["INST_B"] == -0.20  # Factor-implied

    # Total baseline: 15000.00
    # INST_A stressed: 10000 * (1 - 0.35) = 6500.00
    # INST_B stressed: 5000 * (1 - 0.20) = 4000.00
    # Stressed total: 10500.00 -> Loss = 4500.00
    assert res.baseline_value == Decimal("15000.00")
    assert res.stressed_value == Decimal("10500.00")
    assert res.loss_amount == Decimal("4500.00")
    assert pytest.approx(res.loss_fraction, rel=1e-9) == 0.30  # 4500 / 15000 = 0.30
