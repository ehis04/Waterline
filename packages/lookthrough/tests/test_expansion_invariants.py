"""Invariants and safety tests for look-through expansion (depth limit, cycles, unknown funds)."""

from decimal import Decimal
import pytest

from lookthrough.models import FundHoldingsDataset, HoldingRow, PortfolioHolding
from lookthrough.expansion import expand_portfolio


def test_expansion_weight_conservation():
    """Invariant: Exposures + Residuals sum exactly to 100% of portfolio."""
    fund_a = FundHoldingsDataset(
        fund_id="FUND_A",
        as_of="2026-11-25",
        rows=[
            HoldingRow("EQ1", "Corp 1", Decimal("0.60")),
            # 40% unallocated -> residual
        ],
    )
    catalog = {"FUND_A": fund_a}
    portfolio = [
        PortfolioHolding("FUND_A", Decimal("0.70"), is_fund=True),
        PortfolioHolding("DIRECT_EQ", Decimal("0.30"), is_fund=False),
    ]

    res = expand_portfolio(portfolio, catalog)
    total_exp = sum(e.weight for e in res.exposures)
    total_res = sum(r.weight for r in res.residuals)

    assert total_exp + total_res == Decimal("1.000000")
    assert res.coverage_ratio == Decimal("0.7200")  # (0.70*0.60 + 0.30) / 1.0 = 0.42 + 0.30 = 0.72


def test_expansion_cycle_detection():
    """Invariant: Fund cycle does not trigger infinite recursion."""
    # Fund A holds Fund B; Fund B holds Fund A
    fund_a = FundHoldingsDataset(
        fund_id="FUND_A",
        as_of="2026-11-25",
        rows=[HoldingRow("FUND_B", "Fund B", Decimal("1.0"))],
    )
    fund_b = FundHoldingsDataset(
        fund_id="FUND_B",
        as_of="2026-11-25",
        rows=[HoldingRow("FUND_A", "Fund A", Decimal("1.0"))],
    )
    catalog = {"FUND_A": fund_a, "FUND_B": fund_b}
    portfolio = [PortfolioHolding("FUND_A", Decimal("1.0"), is_fund=True)]

    # Run expansion
    res = expand_portfolio(portfolio, catalog)
    assert any("CYCLE" in r.bucket_type or "UNKNOWN" in r.bucket_type for r in res.residuals) or len(res.warnings) > 0


def test_unknown_fund_handling():
    """Invariant: Missing fund is captured as UNKNOWN_FUND without crash."""
    portfolio = [PortfolioHolding("NON_EXISTENT_FUND", Decimal("0.40"), is_fund=True)]
    res = expand_portfolio(portfolio, {})

    assert len(res.residuals) == 1
    assert res.residuals[0].bucket_type == "UNKNOWN_FUND"
    assert res.residuals[0].weight == Decimal("0.40")
