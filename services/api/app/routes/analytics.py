"""Risk, scenario stress-testing, and breaking-point analytics endpoints."""

from decimal import Decimal, ROUND_HALF_UP
import uuid
import numpy as np
from fastapi import APIRouter, HTTPException

from app.contracts import (
    BreakingPointRequest,
    BreakingPointResponse,
    PositionImpact,
    RiskRunRequest,
    RiskRunResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
)
from app.portfolio_data import (
    build_portfolio_snapshot,
    get_funds_catalog,
    get_synthetic_close_prices,
    holdings_market_value,
    resolve_portfolio_key,
)
from risk_core.breaking_point import solve_breaking_point
from risk_core.metrics import calculate_historical_var_es, calculate_mdd
from risk_core.scenarios import apply_hypothetical_shocks

router = APIRouter(prefix="/v1/runs", tags=["Analytics"])


def _round_money(val: float | Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("/risk", response_model=RiskRunResponse)
def run_risk(req: RiskRunRequest) -> RiskRunResponse:
    """Compute historical VaR, Expected Shortfall, and Maximum Drawdown on daily portfolio P&L."""
    key = resolve_portfolio_key(req.portfolio_id)
    snapshot, _ = build_portfolio_snapshot(key)
    price_series = get_synthetic_close_prices()

    # Determine common tail length across all held instruments
    available_lengths = [
        len(price_series[p.instrument_id])
        for p in snapshot.positions
        if p.instrument_id in price_series
    ]
    if not available_lengths:
        raise HTTPException(
            status_code=422,
            detail="No historical price series available for portfolio instruments",
        )

    n_days = min(req.window_days + 1, min(available_lengths))
    if n_days < 11:
        raise HTTPException(
            status_code=422,
            detail="Insufficient price history to compute historical VaR/ES",
        )

    wealth_path: list[float] = []
    for t in range(-n_days, 0):
        day_val = 0.0
        for pos in snapshot.positions:
            series = price_series.get(pos.instrument_id)
            if series:
                day_val += float(pos.quantity) * series[t]
        wealth_path.append(day_val)

    # Losses are positive numbers for calculate_historical_var_es
    losses = [wealth_path[i - 1] - wealth_path[i] for i in range(1, len(wealth_path))]

    var_es_res = calculate_historical_var_es(losses, alpha=req.confidence)
    if var_es_res.is_err or var_es_res.value is None:
        raise HTTPException(status_code=422, detail=var_es_res.error or "VaR calculation failed")
    var_val, es_val = var_es_res.value

    mdd_res = calculate_mdd(wealth_path)
    if mdd_res.is_err or mdd_res.value is None:
        raise HTTPException(status_code=422, detail=mdd_res.error or "MDD calculation failed")
    mdd_val = mdd_res.value

    return RiskRunResponse(
        receipt_id=str(uuid.uuid4()),
        portfolio_id=key,
        confidence=req.confidence,
        window_days=req.window_days,
        currency=snapshot.base_currency,
        var=_round_money(var_val),
        es=_round_money(es_val),
        mdd=Decimal(str(mdd_val)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
    )


@router.post("/scenario", response_model=ScenarioRunResponse)
def run_scenario(req: ScenarioRunRequest) -> ScenarioRunResponse:
    """Apply hypothetical asset return overrides and compute position-level and total P&L impact."""
    key = resolve_portfolio_key(req.portfolio_id)
    snapshot, _ = build_portfolio_snapshot(key)

    overrides = {s.isin: s.override_return for s in req.shocks}
    stress_res = apply_hypothetical_shocks(
        positions=snapshot.positions,
        factor_shocks={},
        factor_betas={},
        asset_overrides=overrides,
    )

    position_impacts: list[PositionImpact] = []
    for pos in snapshot.positions:
        ret = stress_res.asset_returns.get(pos.instrument_id, 0.0)
        baseline_val = pos.market_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        stressed_val = (pos.market_value * Decimal(str(max(0.0, 1.0 + ret)))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        position_impacts.append(
            PositionImpact(
                isin=pos.instrument_id,
                baseline_value=baseline_val,
                stressed_value=stressed_val,
                impact=stressed_val - baseline_val,
                override_return=ret,
            )
        )

    baseline_total = stress_res.baseline_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    stressed_total = stress_res.stressed_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    loss_amount = stress_res.loss_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return ScenarioRunResponse(
        receipt_id=str(uuid.uuid4()),
        portfolio_id=key,
        currency=snapshot.base_currency,
        baseline_value=baseline_total,
        stressed_value=stressed_total,
        total_impact=stressed_total - baseline_total,
        loss_amount=loss_amount,
        loss_fraction=stress_res.loss_fraction,
        position_impacts=position_impacts,
    )


@router.post("/breaking-point", response_model=BreakingPointResponse)
def run_breaking_point(req: BreakingPointRequest) -> BreakingPointResponse:
    """Solve reverse stress-testing breaking point for a given loss threshold and narrative."""
    key = resolve_portfolio_key(req.portfolio_id)
    snapshot, _ = build_portfolio_snapshot(key)
    total_val = holdings_market_value(snapshot)
    catalog = get_funds_catalog()

    # Estimate equity vs rates factor exposures from portfolio weights
    equity_weight = 0.0
    rates_weight = 0.0
    for pos in snapshot.positions:
        w = float(pos.market_value / total_val) if total_val > Decimal("0") else 0.0
        # Bond ETF in synthetic catalog is ZZET00000082
        if pos.instrument_id == "ZZET00000082" or (
            pos.instrument_id in catalog and "bond" in pos.instrument_id.lower()
        ):
            rates_weight += w
        else:
            equity_weight += w

    exposures = np.array([max(equity_weight, 0.05), rates_weight - 0.2 * equity_weight], dtype=float)
    factor_cov = np.array([[0.04, -0.004], [-0.004, 0.0064]], dtype=float)
    cap_first = -0.10 if req.narrative == "equity_capped" else None

    solutions = solve_breaking_point(
        factor_names=["equity", "rates"],
        factor_exposures=exposures,
        factor_cov=factor_cov,
        loss_threshold=req.loss_threshold,
        cap_first_factor=cap_first,
    )

    if req.narrative not in solutions:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown breaking-point narrative '{req.narrative}'. "
            f"Available: {', '.join(solutions.keys())}",
        )

    sol = solutions[req.narrative]
    return BreakingPointResponse(
        receipt_id=str(uuid.uuid4()),
        portfolio_id=key,
        narrative=sol.narrative,
        loss_threshold=Decimal(str(req.loss_threshold)),
        d_star=sol.mahalanobis_distance,
        shocks=sol.shocks,
        gaussian_tail_probability=sol.gaussian_tail_probability,
        loss=Decimal(str(sol.loss)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
    )
