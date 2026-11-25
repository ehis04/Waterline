"""Deterministic tests for Appendix D.1 Accounting fixtures."""

from decimal import Decimal
import pytest

from risk_core.accounting import LedgerEvent, LedgerEventType, fold_ledger
from risk_core.metrics import calculate_mdd
from risk_core.returns import CashFlow, calculate_modified_dietz


def test_fixture_d1_a_two_holdings_shocks():
    """D.1(a) Two holdings £5,000 each; shocks −10% and +4% -> portfolio return −3%, loss £300, final £9,700."""
    initial_h1 = 5000.0
    initial_h2 = 5000.0
    initial_total = initial_h1 + initial_h2

    h1_end = initial_h1 * (1.0 - 0.10)  # 4500
    h2_end = initial_h2 * (1.0 + 0.04)  # 5200
    final_total = h1_end + h2_end       # 9700

    loss = initial_total - final_total
    ret = (final_total - initial_total) / initial_total

    assert final_total == 9700.0
    assert loss == 300.0
    assert pytest.approx(ret, rel=1e-9) == -0.03


def test_fixture_d1_b_foreign_currency_interaction():
    """D.1(b) Foreign asset +10%, foreign currency −5% vs base -> base return 1.10 * 0.95 - 1 = 4.5%."""
    asset_ret = 0.10
    fx_ret = -0.05
    total_ret = (1.0 + asset_ret) * (1.0 + fx_ret) - 1.0
    assert pytest.approx(total_ret, rel=1e-9) == 0.045


def test_fixture_d1_c_maximum_drawdown():
    """D.1(c) Wealth path 100, 120, 90, 108 -> maximum drawdown 25% (120 -> 90)."""
    wealth = [100.0, 120.0, 90.0, 108.0]
    res = calculate_mdd(wealth)
    assert res.is_ok
    assert pytest.approx(res.value, rel=1e-9) == 0.25


def test_fixture_d1_e_deposit_return():
    """D.1(e) Deposit £1,000 into an unchanged £10,000 portfolio -> balance £11,000, investment return 0%."""
    # Deposit happens at mid-period
    cf = [CashFlow(day_fraction=0.5, amount=1000.0)]
    res = calculate_modified_dietz(start_value=10000.0, end_value=11000.0, cash_flows=cf)
    assert res.is_ok
    assert pytest.approx(res.value, abs=1e-9) == 0.0


def test_fixture_d1_f_stock_split_accounting():
    """D.1(f) 2-for-1 split on 10 shares at £100 -> 20 shares at £50; value unchanged; no P&L."""
    events = [
        LedgerEvent("ev_1", "2023-01-01", LedgerEventType.DEPOSIT, None, quantity=Decimal("1000"), currency="GBP"),
        LedgerEvent("ev_2", "2023-01-02", LedgerEventType.BUY, "ZZ0000000018", quantity=Decimal("10"), price=Decimal("100"), currency="GBP"),
        LedgerEvent("ev_3", "2023-01-03", LedgerEventType.SPLIT, "ZZ0000000018", split_ratio=Decimal("2.0")),
    ]
    prices = {"ZZ0000000018": Decimal("50.00")}
    fx = {}

    res = fold_ledger(events, base_currency="GBP", prices=prices, fx_rates=fx)
    assert res.is_ok
    snapshot = res.value
    assert len(snapshot.positions) == 1
    pos = snapshot.positions[0]
    assert pos.quantity == Decimal("20")
    assert pos.current_price == Decimal("50.00")
    assert pos.market_value == Decimal("1000.00")
    assert snapshot.total_market_value == Decimal("1000.00")
