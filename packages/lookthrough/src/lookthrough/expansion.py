"""Portfolio constituent expansion engine with cycle guards and residual accounting."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping

from lookthrough.models import (
    AssetClass,
    ExpandedExposure,
    FundHoldingsDataset,
    LookThroughResult,
    PortfolioHolding,
    ResidualBucket,
)

MAX_EXPANSION_DEPTH = 3


def expand_portfolio(
    portfolio_holdings: list[PortfolioHolding],
    fund_catalog: Mapping[str, FundHoldingsDataset],
    max_depth: int = MAX_EXPANSION_DEPTH,
) -> LookThroughResult:
    """Expand a multi-asset portfolio into underlying constituent exposures and residual buckets."""
    raw_exposures: dict[str, dict] = {}
    routes_counter: dict[str, int] = defaultdict(int)
    residuals: list[ResidualBucket] = []
    warnings: list[str] = []

    def _expand(
        inst_id: str,
        inst_name: str,
        weight: Decimal,
        depth: int,
        path: set[str],
        is_fund: bool,
    ):
        if weight <= Decimal("0"):
            return

        if is_fund:
            if depth >= max_depth:
                warnings.append(f"Maximum expansion depth ({max_depth}) reached for fund {inst_id}; treated as terminal")
                residuals.append(ResidualBucket(bucket_type="DEPTH_LIMIT_RESIDUAL", weight=weight, source_fund_id=inst_id))
                return

            if inst_id in path:
                warnings.append(f"Cycle detected for fund {inst_id}; halted expansion")
                residuals.append(ResidualBucket(bucket_type="CYCLE_RESIDUAL", weight=weight, source_fund_id=inst_id))
                return

            dataset = fund_catalog.get(inst_id)
            if not dataset or not dataset.rows:
                warnings.append(f"Missing holdings data for fund {inst_id}; allocated to UNKNOWN_FUND")
                residuals.append(ResidualBucket(bucket_type="UNKNOWN_FUND", weight=weight, source_fund_id=inst_id))
                return

            if dataset.is_stale:
                warnings.append(f"Holdings data for fund {inst_id} is stale (>45 days)")

            next_path = path | {inst_id}
            fund_row_weight_sum = Decimal("0")

            for row in dataset.rows:
                row_alloc = weight * row.weight
                fund_row_weight_sum += row.weight
                is_subfund = row.constituent_id in fund_catalog
                _expand(
                    inst_id=row.constituent_id,
                    inst_name=row.name,
                    weight=row_alloc,
                    depth=depth + 1,
                    path=next_path,
                    is_fund=is_subfund,
                )

            # Unallocated remainder becomes residual (e.g. fund cash, derivatives, fees)
            unallocated = Decimal("1.000000") - fund_row_weight_sum
            if abs(unallocated) > Decimal("0.000001"):
                residuals.append(
                    ResidualBucket(
                        bucket_type="RESIDUAL",
                        weight=weight * unallocated,
                        source_fund_id=inst_id,
                    )
                )
        else:
            # Direct company / instrument exposure
            routes_counter[inst_id] += 1
            if inst_id not in raw_exposures:
                raw_exposures[inst_id] = {
                    "entity_id": inst_id,
                    "name": inst_name,
                    "weight": weight,
                    "asset_class": AssetClass.EQUITY,
                    "sector": "Unclassified",
                    "country": "ZZ",
                }
            else:
                raw_exposures[inst_id]["weight"] += weight

    # Initial expansion loop
    for p in portfolio_holdings:
        _expand(
            inst_id=p.instrument_id,
            inst_name=p.name or p.instrument_id,
            weight=p.weight,
            depth=0,
            path=set(),
            is_fund=p.is_fund,
        )

    # Build final list of expanded exposures
    exposures: list[ExpandedExposure] = []
    duplicate_weight = Decimal("0")

    for entity_id, data in raw_exposures.items():
        w = data["weight"]
        routes = routes_counter[entity_id]
        if routes >= 2:
            duplicate_weight += w
        exposures.append(
            ExpandedExposure(
                entity_id=entity_id,
                name=data["name"],
                weight=w,
                asset_class=data["asset_class"],
                sector=data["sector"],
                country=data["country"],
                routes_count=routes,
            )
        )

    # Sort exposures descending by weight
    exposures.sort(key=lambda x: x.weight, reverse=True)

    # Calculate Look-Through HHI and N_effective
    hhi = sum((e.weight ** 2) for e in exposures) if exposures else Decimal("0")
    n_eff = (Decimal("1.0") / hhi).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if hhi > Decimal("0") else Decimal("0")

    total_exp_weight = sum((e.weight for e in exposures), start=Decimal("0"))
    total_res_weight = sum((r.weight for r in residuals), start=Decimal("0"))
    total_weight = total_exp_weight + total_res_weight
    coverage = (total_exp_weight / total_weight) if total_weight > Decimal("0") else Decimal("1.0")

    return LookThroughResult(
        exposures=exposures,
        residuals=residuals,
        coverage_ratio=coverage.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        duplicate_exposure_weight=duplicate_weight.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        hhi=hhi.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        n_effective=n_eff,
        warnings=warnings,
    )
