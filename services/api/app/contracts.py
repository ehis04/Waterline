"""Standard Pydantic API schemas and error contract definitions."""

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="Machine-readable error identifier")
    message: str = Field(description="Human-readable description of the error")
    request_id: str = Field(description="Unique correlation ID for tracing")
    retryable: bool = Field(default=False, description="Whether repeating the request without changes may succeed")
    details: dict[str, Any] = Field(default_factory=dict, description="Context-specific diagnostic information")


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ReceiptVerifyRequest(BaseModel):
    receipt: dict[str, Any] = Field(description="Full Receipt Schema v2 document to verify")


class ReceiptVerifyResponse(BaseModel):
    valid: bool
    run_id: str
    receipt_sha256: str
    reason: str | None = None


class PairwiseOverlapItem(BaseModel):
    fund_a: str
    fund_b: str
    weight_overlap: float
    bounds: tuple[float, float]
    common_entities_count: int


class PublicOverlapResponse(BaseModel):
    isins: list[str]
    pairwise: list[PairwiseOverlapItem]


class PortfolioSummary(BaseModel):
    portfolio_id: str
    name: str
    base_currency: str
    positions_count: int
    total_market_value: Decimal


class PositionSchema(BaseModel):
    instrument_id: str
    ticker: str | None = None
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal
    market_value: Decimal
    currency: str
    weight: Decimal


class PortfolioDetail(BaseModel):
    portfolio_id: str
    name: str
    base_currency: str
    total_market_value: Decimal
    cash: Decimal
    coverage_ratio: Decimal
    positions: list[PositionSchema]


class XRayPosition(BaseModel):
    entity_id: str
    name: str
    weight: Decimal
    asset_class: str
    sector: str
    country: str
    routes_count: int


class XRayResponse(BaseModel):
    portfolio_id: str
    positions: list[XRayPosition]
    coverage_ratio: Decimal
    duplicate_exposure_weight: Decimal
    hhi: Decimal
    n_effective: Decimal
    warnings: list[str]


class RiskRunRequest(BaseModel):
    portfolio_id: str
    confidence: float = Field(default=0.95, gt=0.0, lt=1.0)
    window_days: int = Field(default=252, ge=10, le=2000)


class RiskRunResponse(BaseModel):
    receipt_id: str
    portfolio_id: str
    confidence: float
    window_days: int
    currency: str
    var: Decimal
    es: Decimal
    mdd: Decimal


class ScenarioShock(BaseModel):
    isin: str
    override_return: float


class ScenarioRunRequest(BaseModel):
    portfolio_id: str
    shocks: list[ScenarioShock]


class PositionImpact(BaseModel):
    isin: str
    baseline_value: Decimal
    stressed_value: Decimal
    impact: Decimal
    override_return: float


class ScenarioRunResponse(BaseModel):
    receipt_id: str
    portfolio_id: str
    currency: str
    baseline_value: Decimal
    stressed_value: Decimal
    total_impact: Decimal
    loss_amount: Decimal
    loss_fraction: float
    position_impacts: list[PositionImpact]


class BreakingPointRequest(BaseModel):
    portfolio_id: str
    loss_threshold: float = Field(default=0.15, gt=0.0)
    narrative: str = Field(default="unconstrained")


class BreakingPointResponse(BaseModel):
    receipt_id: str
    portfolio_id: str
    narrative: str
    loss_threshold: Decimal
    d_star: float
    shocks: dict[str, float]
    gaussian_tail_probability: float | None
    loss: Decimal
