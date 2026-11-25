"""Quantitative risk metrics: VaR, Expected Shortfall, Maximum Drawdown, EWMA, and HHI."""

import math
from typing import Sequence
import numpy as np
from scipy import stats

from risk_core.types import Result, WarningMessage, Severity


def calculate_mdd(wealth_path: Sequence[float]) -> Result[float, str]:
    """Calculate Maximum Drawdown from a wealth path.
    
    Formula: max_t ((Peak_t - W_t) / Peak_t)
    """
    if len(wealth_path) < 2:
        return Result.ok(0.0)

    max_dd = 0.0
    peak = wealth_path[0]

    for val in wealth_path:
        if val > peak:
            peak = val
        elif peak > 0.0:
            dd = (peak - val) / peak
            if dd > max_dd:
                max_dd = dd

    return Result.ok(max_dd)


def calculate_historical_var_es(
    losses: Sequence[float],
    alpha: float = 0.95,
) -> Result[tuple[float, float], str]:
    """Calculate Historical Value at Risk (VaR) and Expected Shortfall (ES).
    
    Convention (Q-13, D.2):
    Losses are positive numbers.
    For N sorted losses, VaR is the alpha quantile.
    ES is the arithmetic mean of the (1 - alpha) tail losses exceeding or equal to VaR.
    """
    n = len(losses)
    if n < 10:
        return Result.err("Insufficient sample size for historical VaR/ES calculation (minimum 10)")

    warnings: list[WarningMessage] = []
    if n < 60:
        warnings.append(
            WarningMessage(
                code="SMALL_SAMPLE_VAR",
                message=f"Sample size {n} is below recommended gate of 60 for tail estimation",
                severity=Severity.WARNING,
            )
        )

    sorted_losses = sorted(losses)
    # Target index for alpha quantile
    k = int(math.ceil(alpha * n))  # e.g., alpha=0.95, n=100 -> k=95
    # 0-based index for k-th smallest is k - 1
    var_idx = min(k - 1, n - 1)
    var_val = sorted_losses[var_idx]

    # Tail losses are the worst (n - k + 1) or worst int((1 - alpha)*n) losses
    tail_count = max(1, n - k)
    if tail_count == 0:
        tail_losses = [sorted_losses[-1]]
    else:
        tail_losses = sorted_losses[n - tail_count:]

    es_val = sum(tail_losses) / len(tail_losses)
    return Result.ok((var_val, es_val), warnings=warnings)


def calculate_gaussian_var_es(
    mean_loss: float,
    std_loss: float,
    alpha: float = 0.95,
) -> tuple[float, float]:
    """Calculate parametric Gaussian VaR and Expected Shortfall."""
    z = stats.norm.ppf(alpha)
    pdf_z = stats.norm.pdf(z)
    var = mean_loss + z * std_loss
    es = mean_loss + std_loss * (pdf_z / (1.0 - alpha))
    return var, es


def calculate_ewma_volatility(
    returns: Sequence[float],
    decay: float = 0.94,
) -> float:
    """Calculate exponentially weighted moving average volatility (annualized assuming 252 days)."""
    if len(returns) < 2:
        return 0.0

    var = 0.0
    for r in returns:
        var = decay * var + (1.0 - decay) * (r ** 2)

    return math.sqrt(var * 252.0)


def calculate_hhi(weights: Sequence[float]) -> tuple[float, float]:
    """Calculate Herfindahl-Hirschman Index and Effective Number of Positions.
    
    HHI = sum(w_i^2)
    N_eff = 1 / HHI
    """
    total = sum(weights)
    if total <= 0.0:
        return 0.0, 0.0

    norm_w = [w / total for w in weights]
    hhi = sum(w ** 2 for w in norm_w)
    n_eff = 1.0 / hhi if hhi > 0.0 else 0.0
    return hhi, n_eff


def calculate_diversification_ratio(
    weights: Sequence[float],
    individual_volatilities: Sequence[float],
    portfolio_volatility: float,
) -> float:
    """Calculate Diversification Ratio (DR).
    
    DR = sum(w_i * sigma_i) / sigma_p
    """
    if portfolio_volatility <= 1e-12:
        return 1.0
    weighted_vol_sum = sum(w * vol for w, vol in zip(weights, individual_volatilities))
    return weighted_vol_sum / portfolio_volatility
