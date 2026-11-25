"""Risk Diff: decomposing changes in risk into holdings and market contributions via Shapley values."""

from dataclasses import dataclass
import numpy as np
from risk_core.euler import calculate_portfolio_volatility


@dataclass(frozen=True)
class RiskDiffResult:
    vol_start: float
    vol_end: float
    total_change: float
    holdings_contribution: float  # phi_H
    market_contribution: float    # phi_M


def calculate_risk_diff(
    weights_a: np.ndarray,
    cov_a: np.ndarray,
    weights_b: np.ndarray,
    cov_b: np.ndarray,
) -> RiskDiffResult:
    """Compute 2-factor Shapley decomposition of portfolio volatility change from state A to state B.
    
    Evaluations:
        f_empty: weights A, market A
        f_h: weights B, market A
        f_m: weights A, market B
        f_hm: weights B, market B
    """
    f_empty = calculate_portfolio_volatility(weights_a, cov_a)
    f_h = calculate_portfolio_volatility(weights_b, cov_a)
    f_m = calculate_portfolio_volatility(weights_a, cov_b)
    f_hm = calculate_portfolio_volatility(weights_b, cov_b)

    phi_h = 0.5 * ((f_h - f_empty) + (f_hm - f_m))
    phi_m = 0.5 * ((f_m - f_empty) + (f_hm - f_h))
    total = f_hm - f_empty

    return RiskDiffResult(
        vol_start=f_empty,
        vol_end=f_hm,
        total_change=total,
        holdings_contribution=phi_h,
        market_contribution=phi_m,
    )
