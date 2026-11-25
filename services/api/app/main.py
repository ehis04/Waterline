"""Main FastAPI application entry point for Waterline API."""

import uuid
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.contracts import ErrorResponse
from app.routes import analytics, demo, health, portfolio, public_overlap, receipts

app = FastAPI(
    title="Waterline Financial Risk API",
    description="Open-core portfolio risk workbench and verifiable analytics engine",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_cache_control_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    # Default private cache control for security
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "private, no-store"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    content = ErrorResponse(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        request_id=request_id,
        retryable=exc.status_code >= 500,
        details={},
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    content = ErrorResponse(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred.",
        request_id=request_id,
        retryable=True,
        details={"error_type": type(exc).__name__},
    ).model_dump()
    return JSONResponse(status_code=500, content=content)


# Register routers
app.include_router(health.router)
app.include_router(demo.router)
app.include_router(public_overlap.router)
app.include_router(receipts.router)
app.include_router(portfolio.router)
app.include_router(analytics.router)
