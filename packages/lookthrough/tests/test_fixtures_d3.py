"""Deterministic tests for Appendix D.3 Look-through and overlap fixtures."""

from decimal import Decimal
import pytest

from lookthrough.models import FundHoldingsDataset, HoldingRow, PortfolioHolding
from lookthrough.expansion import expand_portfolio
from lookthrough.overlap import calculate_fund_overlap


def test_fixture_d3_lookthrough_and_overlap():
    """D.3 Look-through and overlap:
    Fund G: Alpha 4%, Beta 3.5%, Gamma 2.5%, Delta 1%
    Fund U: Alpha 7%, Beta 6%, Gamma 4.5%, Delta 2%
    Fund N: Alpha 9%, Beta 8%, Gamma 7%, Epsilon 5%

    Portfolio: 50% G, 30% U, 20% N
    Look-through: Alpha 5.90%, Beta 5.15%, Gamma 4.00%, Delta 1.10%, Epsilon 1.00%; top-3 = 15.05%
    Pairwise overlap: O(G,U) = 11.0%, O(G,N) = 10.0%, O(U,N) = 17.5%
    """
    fund_g = FundHoldingsDataset(
        fund_id="FUND_G",
        as_of="2026-11-25",
        rows=[
            HoldingRow("ALPHA", "Alpha Corp", Decimal("0.040")),
            HoldingRow("BETA", "Beta Corp", Decimal("0.035")),
            HoldingRow("GAMMA", "Gamma Corp", Decimal("0.025")),
            HoldingRow("DELTA", "Delta Corp", Decimal("0.010")),
        ],
    )

    fund_u = FundHoldingsDataset(
        fund_id="FUND_U",
        as_of="2026-11-25",
        rows=[
            HoldingRow("ALPHA", "Alpha Corp", Decimal("0.070")),
            HoldingRow("BETA", "Beta Corp", Decimal("0.060")),
            HoldingRow("GAMMA", "Gamma Corp", Decimal("0.045")),
            HoldingRow("DELTA", "Delta Corp", Decimal("0.020")),
        ],
    )

    fund_n = FundHoldingsDataset(
        fund_id="FUND_N",
        as_of="2026-11-25",
        rows=[
            HoldingRow("ALPHA", "Alpha Corp", Decimal("0.090")),
            HoldingRow("BETA", "Beta Corp", Decimal("0.080")),
            HoldingRow("GAMMA", "Gamma Corp", Decimal("0.070")),
            HoldingRow("EPSILON", "Epsilon Corp", Decimal("0.050")),
        ],
    )

    catalog = {
        "FUND_G": fund_g,
        "FUND_U": fund_u,
        "FUND_N": fund_n,
    }

    portfolio = [
        PortfolioHolding("FUND_G", Decimal("0.50"), is_fund=True),
        PortfolioHolding("FUND_U", Decimal("0.30"), is_fund=True),
        PortfolioHolding("FUND_N", Decimal("0.20"), is_fund=True),
    ]

    # 1. Expand Portfolio
    res = expand_portfolio(portfolio, catalog)
    exp_map = {e.entity_id: e.weight for e in res.exposures}

    assert exp_map["ALPHA"] == Decimal("0.059000")
    assert exp_map["BETA"] == Decimal("0.051500")
    assert exp_map["GAMMA"] == Decimal("0.040000")
    assert exp_map["DELTA"] == Decimal("0.011000")
    assert exp_map["EPSILON"] == Decimal("0.010000")

    top3 = exp_map["ALPHA"] + exp_map["BETA"] + exp_map["GAMMA"]
    assert top3 == Decimal("0.150500")

    # 2. Pairwise Overlap
    o_gu = calculate_fund_overlap(fund_g, fund_u)
    assert o_gu.weight_overlap == Decimal("0.1100")

    o_gn = calculate_fund_overlap(fund_g, fund_n)
    assert o_gn.weight_overlap == Decimal("0.1000")

    o_un = calculate_fund_overlap(fund_u, fund_n)
    assert o_un.weight_overlap == Decimal("0.1750")

    # 3. Duplicate Exposure
    # Alpha, Beta, Gamma, Delta are reached by >= 2 routes
    # Epsilon is reached by only 1 route (Fund N)
    assert exp_map["ALPHA"] + exp_map["BETA"] + exp_map["GAMMA"] + exp_map["DELTA"] == res.duplicate_exposure_weight
