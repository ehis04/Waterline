"""Breaking Point: reverse stress testing solving for minimum Mahalanobis distance scenarios."""

from dataclasses import dataclass
import math
import numpy as np
from scipy import stats


@dataclass(frozen=True)
class BreakingPointSolution:
    narrative: str
    shocks: dict[str, float]
    mahalanobis_distance: float
    gaussian_tail_probability: float | None
    loss: float


def solve_breaking_point(
    factor_names: list[str],
    factor_exposures: np.ndarray,  # vector b
    factor_cov: np.ndarray,        # matrix C
    loss_threshold: float,         # T > 0
    cap_first_factor: float | None = None,
) -> dict[str, BreakingPointSolution]:
    """Solve reverse stress testing narratives for a given loss threshold."""
    if loss_threshold <= 0.0:
        raise ValueError("Loss threshold T must be strictly positive")

    b = factor_exposures
    a = -b  # Loss L(s) = a^T * s
    c_mat = factor_cov
    t = loss_threshold

    denom = float(a.T @ c_mat @ a)
    if denom <= 1e-15:
        raise ValueError("Zero factor variance along exposure direction")

    c_inv = np.linalg.pinv(c_mat)
    solutions: dict[str, BreakingPointSolution] = {}

    # 1. Unconstrained Closed-Form Solution
    s_unconstrained = (c_mat @ a) * (t / denom)
    d_unconstrained = t / math.sqrt(denom)
    prob_unconstrained = 1.0 - stats.norm.cdf(d_unconstrained)
    shocks_unconstrained = {name: float(val) for name, val in zip(factor_names, s_unconstrained)}

    solutions["unconstrained"] = BreakingPointSolution(
        narrative="unconstrained",
        shocks=shocks_unconstrained,
        mahalanobis_distance=d_unconstrained,
        gaussian_tail_probability=prob_unconstrained,
        loss=float(a.T @ s_unconstrained),
    )

    # 2. Equity-only narrative (if 2 factors: fix factor 2 to 0.0)
    if len(b) >= 2:
        s1 = t / a[0]
        s_eq_only = np.zeros_like(b)
        s_eq_only[0] = s1
        d_eq_only = math.sqrt(float(s_eq_only.T @ c_inv @ s_eq_only))
        shocks_eq = {name: float(val) for name, val in zip(factor_names, s_eq_only)}
        solutions["equity_only"] = BreakingPointSolution(
            narrative="equity_only",
            shocks=shocks_eq,
            mahalanobis_distance=d_eq_only,
            gaussian_tail_probability=1.0 - stats.norm.cdf(d_eq_only),
            loss=float(a.T @ s_eq_only),
        )

    # 3. Factor 1 Capped (e.g. Equity shock capped at >= -10%)
    if cap_first_factor is not None and len(b) >= 2:
        s1_capped = cap_first_factor
        # a[0]*s1 + a[1]*s2 = t -> s2 = (t - a[0]*s1) / a[1]
        s2 = (t - a[0] * s1_capped) / a[1]
        s_capped = np.array([s1_capped, s2])
        d_capped = math.sqrt(float(s_capped.T @ c_inv @ s_capped))
        shocks_capped = {name: float(val) for name, val in zip(factor_names, s_capped)}
        solutions["equity_capped"] = BreakingPointSolution(
            narrative="equity_capped",
            shocks=shocks_capped,
            mahalanobis_distance=d_capped,
            gaussian_tail_probability=1.0 - stats.norm.cdf(d_capped),
            loss=float(a.T @ s_capped),
        )

    return solutions
