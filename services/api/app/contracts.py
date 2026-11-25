"""Standard Pydantic API schemas and error contract definitions."""

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
