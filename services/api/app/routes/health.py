"""Health check endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.contracts import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Check if the API container process is alive."""
    return HealthResponse(
        status="live",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Check if the API service is ready to handle traffic."""
    return HealthResponse(
        status="ready",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
