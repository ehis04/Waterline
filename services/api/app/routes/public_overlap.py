"""Public Overlap Checker endpoint."""

from decimal import Decimal
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

from app.contracts import PairwiseOverlapItem, PublicOverlapResponse
from lookthrough.models import FundHoldingsDataset, HoldingRow
from lookthrough.overlap import calculate_fund_overlap

router = APIRouter(prefix="/v1/public", tags=["Public"])

_SYNTHETIC_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "synthetic"


def _get_funds_catalog() -> dict[str, FundHoldingsDataset]:
    funds_path = _SYNTHETIC_DIR / "funds.json"
    if not funds_path.exists():
        return {}
    with open(funds_path, "r") as f:
        data = json.load(f)

    catalog = {}
    for item in data:
        rows = [
            HoldingRow(
                constituent_id=c["constituent_isin"],
                name=c["name"],
                weight=Decimal(str(c["weight"])),
                sector=c.get("sector", "Unclassified"),
                country=c.get("country", "ZZ"),
            )
            for c in item.get("constituents", [])
        ]
        catalog[item["isin"]] = FundHoldingsDataset(
            fund_id=item["isin"],
            as_of="2026-11-25",
            rows=rows,
        )
    return catalog


@router.get("/overlap", response_model=PublicOverlapResponse)
def check_overlap(
    isins: str = Query(..., description="Comma-separated fund ISINs to evaluate"),
) -> PublicOverlapResponse:
    """Calculate pairwise fund weight overlap and bounds for provided ISINs."""
    isin_list = [i.strip().upper() for i in isins.split(",") if i.strip()]
    if len(isin_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two fund ISINs are required for overlap checking",
        )

    catalog = _get_funds_catalog()
    for isin in isin_list:
        if isin not in catalog:
            raise HTTPException(
                status_code=404,
                detail=f"Fund ISIN '{isin}' not found in public funds catalog",
            )

    pairwise_items: list[PairwiseOverlapItem] = []
    n = len(isin_list)
    for i in range(n):
        for j in range(i + 1, n):
            fa = catalog[isin_list[i]]
            fb = catalog[isin_list[j]]
            res = calculate_fund_overlap(fa, fb)
            pairwise_items.append(
                PairwiseOverlapItem(
                    fund_a=fa.fund_id,
                    fund_b=fb.fund_id,
                    weight_overlap=float(res.weight_overlap),
                    bounds=(float(res.min_overlap_bound), float(res.max_overlap_bound)),
                    common_entities_count=res.common_entities_count,
                )
            )

    return PublicOverlapResponse(
        isins=isin_list,
        pairwise=pairwise_items,
    )
