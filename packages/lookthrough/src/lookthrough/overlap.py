"""Pairwise ETF overlap metrics and honest bounds under unallocated weights."""

from decimal import Decimal, ROUND_HALF_UP
from lookthrough.models import FundHoldingsDataset, PairwiseOverlapResult


def calculate_fund_overlap(
    fund_a: FundHoldingsDataset,
    fund_b: FundHoldingsDataset,
) -> PairwiseOverlapResult:
    """Calculate pairwise holdings weight overlap, honest bounds, and Jaccard count overlap."""
    weights_a = {row.constituent_id: row.weight for row in fund_a.rows}
    weights_b = {row.constituent_id: row.weight for row in fund_b.rows}

    all_entities = set(weights_a.keys()) | set(weights_b.keys())
    common_entities = set(weights_a.keys()) & set(weights_b.keys())

    known_overlap = Decimal("0")
    for eid in common_entities:
        known_overlap += min(weights_a[eid], weights_b[eid])

    total_weight_a = sum(weights_a.values())
    total_weight_b = sum(weights_b.values())

    unknown_a = max(Decimal("0"), Decimal("1.000000") - total_weight_a)
    unknown_b = max(Decimal("0"), Decimal("1.000000") - total_weight_b)

    max_bound = min(Decimal("1.000000"), known_overlap + min(unknown_a, unknown_b))

    jaccard = (
        (Decimal(len(common_entities)) / Decimal(len(all_entities)))
        if all_entities
        else Decimal("0")
    )

    return PairwiseOverlapResult(
        fund_a_id=fund_a.fund_id,
        fund_b_id=fund_b.fund_id,
        weight_overlap=known_overlap.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        min_overlap_bound=known_overlap.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        max_overlap_bound=max_bound.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        count_overlap_jaccard=jaccard.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        common_entities_count=len(common_entities),
    )
