"""Demo endpoints serving synthetic dataset universe."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/demo", tags=["Demo"])

_SYNTHETIC_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "synthetic"


def _load_json(filename: str) -> dict | list:
    filepath = _SYNTHETIC_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Synthetic data pack file {filename} not found. Please run seed script.",
        )
    with open(filepath, "r") as f:
        return json.load(f)


@router.get("/portfolios")
def list_demo_portfolios():
    """Retrieve demo portfolios with complete transaction histories."""
    return _load_json("portfolios.json")


@router.get("/funds")
def list_demo_funds():
    """Retrieve synthetic UCITS funds catalog."""
    return _load_json("funds.json")


@router.get("/companies")
def list_demo_companies():
    """Retrieve synthetic companies list."""
    return _load_json("companies.json")
