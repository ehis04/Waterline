"""Euler risk decomposition: marginal contributions and component risk contributions."""

import math
import numpy as np


def calculate_portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculate portfolio volatility: sigma_p = sqrt(w^T * Sigma * w)."""
    var = float(weights.T @ cov_matrix @ weights)
    return math.sqrt(max(0.0, var))


def calculate_euler_contributions(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Calculate Euler risk contributions.
    
    Returns:
        (portfolio_volatility, marginal_contributions, risk_contributions)
    Where:
        MRC = (cov_matrix @ weights) / sigma_p
        RC = weights * MRC
        sum(RC) == sigma_p
    """
    sigma_p = calculate_portfolio_volatility(weights, cov_matrix)
    if sigma_p <= 1e-12:
        zero_arr = np.zeros_like(weights)
        return 0.0, zero_arr, zero_arr

    mrc = (cov_matrix @ weights) / sigma_p
    rc = weights * mrc
    return sigma_p, mrc, rc
