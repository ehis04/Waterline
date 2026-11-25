"""Domain models for look-through constituent expansion and ETF overlap analysis."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    BOND = "BOND"
    COMMODITY = "COMMODITY"
    CASH = "CASH"
    DERIVATIVE = "DERIVATIVE"
    OTHER = "OTHER"


@dataclass(frozen=True)
class HoldingRow:
    constituent_id: str
    name: str
    weight: Decimal
    asset_class: AssetClass = AssetClass.EQUITY
    sector: str = "Unclassified"
    country: str = "ZZ"
    currency: str = "USD"


@dataclass(frozen=True)
class FundHoldingsDataset:
    fund_id: str
    as_of: str
    rows: list[HoldingRow]
    available_at: str | None = None
    is_stale: bool = False


@dataclass(frozen=True)
class PortfolioHolding:
    instrument_id: str
    weight: Decimal
    is_fund: bool = False
    name: str | None = None


@dataclass(frozen=True)
class ExpandedExposure:
    entity_id: str
    name: str
    weight: Decimal
    asset_class: AssetClass
    sector: str
    country: str
    routes_count: int


@dataclass(frozen=True)
class ResidualBucket:
    bucket_type: str
    weight: Decimal
    source_fund_id: str | None = None


@dataclass
class LookThroughResult:
    exposures: list[ExpandedExposure]
    residuals: list[ResidualBucket]
    coverage_ratio: Decimal
    duplicate_exposure_weight: Decimal
    hhi: Decimal
    n_effective: Decimal
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PairwiseOverlapResult:
    fund_a_id: str
    fund_b_id: str
    weight_overlap: Decimal
    min_overlap_bound: Decimal
    max_overlap_bound: Decimal
    count_overlap_jaccard: Decimal
    common_entities_count: int
