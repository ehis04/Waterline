"""Portfolio performance calculations: TWR, Modified Dietz, and Money-Weighted Return (MWR/IRR)."""

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Sequence

from risk_core.types import Result, WarningMessage, Severity


@dataclass(frozen=True)
class CashFlow:
    day_fraction: float  # t_i / T (0.0 to 1.0)
    amount: float        # Positive for external contribution, negative for withdrawal


def calculate_twr(subperiod_returns: Sequence[float]) -> float:
    """Calculate Time-Weighted Return (TWR) by chain-linking subperiod returns."""
    product = 1.0
    for r in subperiod_returns:
        product *= 1.0 + r
    return product - 1.0


def calculate_modified_dietz(
    start_value: float,
    end_value: float,
    cash_flows: Sequence[CashFlow],
) -> Result[float, str]:
    """Calculate Modified Dietz return.
    
    Formula: (V_1 - V_0 - C) / (V_0 + sum(C_i * W_i))
    where W_i = 1.0 - day_fraction.
    """
    if start_value <= 0.0 and end_value <= 0.0:
        return Result.err("Modified Dietz undefined for zero or negative start and end values")

    total_net_cf = sum(cf.amount for cf in cash_flows)
    weighted_cf = sum(cf.amount * (1.0 - cf.day_fraction) for cf in cash_flows)
    denom = start_value + weighted_cf

    if abs(denom) < 1e-12:
        return Result.err("Denominator in Modified Dietz is zero")

    gain = end_value - start_value - total_net_cf
    ret = gain / denom
    return Result.ok(ret)


def calculate_mwr_irr(
    start_value: float,
    end_value: float,
    cash_flows: Sequence[CashFlow],
    max_iter: int = 100,
    tol: float = 1e-8,
) -> Result[float, str]:
    """Calculate Money-Weighted Return (Internal Rate of Return) via Brent's method."""
    # Net Present Value objective function
    def npv(r: float) -> float:
        # V_0 + sum(C_i / (1 + r)^t_i) - V_1 / (1 + r)^1.0 = 0
        if r <= -0.999999:
            return float("inf")
        val = start_value
        for cf in cash_flows:
            val += cf.amount / ((1.0 + r) ** cf.day_fraction)
        val -= end_value / (1.0 + r)
        return val

    # Bracket search around -99% to +1000%
    r_low = -0.99
    r_high = 10.0
    f_low = npv(r_low)
    f_high = npv(r_high)

    if f_low * f_high > 0:
        # Try narrower brackets or return Dietz approximation
        dietz = calculate_modified_dietz(start_value, end_value, cash_flows)
        if dietz.is_ok and dietz.value is not None:
            return Result.ok(
                dietz.value,
                warnings=[
                    WarningMessage(
                        code="IRR_BRACKET_FALLBACK",
                        message="Could not bracket IRR root; returned Modified Dietz approximation",
                        severity=Severity.WARNING,
                    )
                ],
            )
        return Result.err("Failed to bracket IRR solution root")

    # Bisection / Secant iteration
    a = r_low
    b = r_high
    fa = f_low
    fb = f_high

    for _ in range(max_iter):
        if abs(fb) < tol or abs(b - a) < tol:
            return Result.ok(b)
        # Secant step
        denom = fb - fa
        if abs(denom) < 1e-15:
            m = 0.5 * (a + b)
        else:
            m = b - fb * (b - a) / denom
            if not (a < m < b or b < m < a):
                m = 0.5 * (a + b)
        
        fm = npv(m)
        if abs(fm) < tol:
            return Result.ok(m)
        if fa * fm < 0:
            b = m
            fb = fm
        else:
            a = m
            fa = fm

    return Result.ok(b)
