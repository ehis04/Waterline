"""Hypothetical stress testing, asset overrides rule (Q-31), and historical window replay."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from risk_core.types import Position


@dataclass(frozen=True)
class StressResult:
    baseline_value: Decimal
    stressed_value: Decimal
    loss_amount: Decimal
    loss_fraction: float
    asset_returns: dict[str, float]


def apply_hypothetical_shocks(
    positions: Sequence[Position],
    factor_shocks: Mapping[str, float],
    factor_betas: Mapping[str, Mapping[str, float]],  # asset_id -> {factor: beta}
    asset_overrides: Mapping[str, float] | None = None,  # Rule Q-31: direct asset overrides replace factor return
) -> StressResult:
    """Apply factor shocks and direct asset overrides to positions.
    
    Rule Q-31: Direct asset overrides replace, not add to, factor-implied returns.
    """
    overrides = asset_overrides or {}
    asset_returns: dict[str, float] = {}

    baseline_total = Decimal("0")
    stressed_total = Decimal("0")

    for p in positions:
        inst = p.instrument_id
        pos_val = p.market_value
        baseline_total += pos_val

        if inst in overrides:
            r = overrides[inst]
        elif inst in factor_betas:
            betas = factor_betas[inst]
            r = sum(betas.get(f, 0.0) * s for f, s in factor_shocks.items())
        else:
            r = 0.0

        asset_returns[inst] = r
        stressed_pos_val = pos_val * Decimal(str(max(0.0, 1.0 + r)))
        stressed_total += stressed_pos_val

    loss = baseline_total - stressed_total
    loss_pct = float(loss / baseline_total) if baseline_total > Decimal("0") else 0.0

    return StressResult(
        baseline_value=baseline_total,
        stressed_value=stressed_total,
        loss_amount=loss,
        loss_fraction=loss_pct,
        asset_returns=asset_returns,
    )
