"""Portfolio CRUD and look-through X-Ray endpoints."""

from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter

from app.contracts import (
    PortfolioDetail,
    PortfolioSummary,
    PositionSchema,
    XRayPosition,
    XRayResponse,
)
from app.portfolio_data import (
    build_portfolio_snapshot,
    get_funds_catalog,
    get_portfolio_name,
    holdings_market_value,
    list_portfolio_keys,
    resolve_portfolio_key,
)
from lookthrough.expansion import expand_portfolio
from lookthrough.models import PortfolioHolding

router = APIRouter(prefix="/v1/portfolios", tags=["Portfolios"])


@router.get("", response_model=list[PortfolioSummary])
def list_portfolios() -> list[PortfolioSummary]:
    """List available demo portfolios with summary valuation metrics."""
    summaries: list[PortfolioSummary] = []
    for key in list_portfolio_keys():
        snapshot, _ = build_portfolio_snapshot(key)
        total_val = holdings_market_value(snapshot)
        summaries.append(
            PortfolioSummary(
                portfolio_id=key,
                name=get_portfolio_name(key),
                base_currency=snapshot.base_currency,
                positions_count=len(snapshot.positions),
                total_market_value=total_val,
            )
        )
    return summaries


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(portfolio_id: str) -> PortfolioDetail:
    """Retrieve a single portfolio with its valued positions."""
    key = resolve_portfolio_key(portfolio_id)
    snapshot, tickers = build_portfolio_snapshot(key)
    total_val = holdings_market_value(snapshot)

    positions: list[PositionSchema] = []
    for pos in snapshot.positions:
        weight = (
            (pos.market_value / total_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if total_val > Decimal("0")
            else Decimal("0")
        )
        positions.append(
            PositionSchema(
                instrument_id=pos.instrument_id,
                ticker=tickers.get(pos.instrument_id),
                quantity=pos.quantity,
                cost_basis=pos.cost_basis.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                current_price=pos.current_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                market_value=pos.market_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                currency=pos.currency,
                weight=weight,
            )
        )

    return PortfolioDetail(
        portfolio_id=key,
        name=get_portfolio_name(key),
        base_currency=snapshot.base_currency,
        total_market_value=total_val,
        cash=snapshot.cash,
        coverage_ratio=snapshot.coverage_ratio,
        positions=positions,
    )


@router.get("/{portfolio_id}/xray", response_model=XRayResponse)
def get_portfolio_xray(portfolio_id: str) -> XRayResponse:
    """Run look-through expansion on a portfolio and return flat leaf positions with weights."""
    key = resolve_portfolio_key(portfolio_id)
    snapshot, tickers = build_portfolio_snapshot(key)
    total_val = holdings_market_value(snapshot)
    catalog = get_funds_catalog()

    holdings: list[PortfolioHolding] = []
    for pos in snapshot.positions:
        weight = (pos.market_value / total_val) if total_val > Decimal("0") else Decimal("0")
        holdings.append(
            PortfolioHolding(
                instrument_id=pos.instrument_id,
                weight=weight,
                is_fund=pos.instrument_id in catalog,
                name=tickers.get(pos.instrument_id, pos.instrument_id),
            )
        )

    result = expand_portfolio(holdings, catalog)
    leaf_positions = [
        XRayPosition(
            entity_id=exp.entity_id,
            name=exp.name,
            weight=exp.weight.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            asset_class=exp.asset_class.value,
            sector=exp.sector,
            country=exp.country,
            routes_count=exp.routes_count,
        )
        for exp in result.exposures
    ]

    return XRayResponse(
        portfolio_id=key,
        positions=leaf_positions,
        coverage_ratio=result.coverage_ratio,
        duplicate_exposure_weight=result.duplicate_exposure_weight,
        hhi=result.hhi,
        n_effective=result.n_effective,
        warnings=result.warnings,
    )
