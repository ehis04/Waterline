"""Shared synthetic portfolio, fund catalog, and price series loaders."""

from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import json
from pathlib import Path

from fastapi import HTTPException

from data_adapters.synthetic.generator import SyntheticMarketGenerator
from lookthrough.models import FundHoldingsDataset, HoldingRow
from risk_core.accounting import LedgerEvent, LedgerEventType, fold_ledger
from risk_core.types import ValuationSnapshot

_SYNTHETIC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic"

_PORTFOLIO_METADATA: dict[str, dict[str, str]] = {
    "overlapping_etfs": {
        "name": "Three Overlapping ETFs",
        "alias": "p_overlapping",
    },
    "uk_wrapper_split": {
        "name": "UK Wrapper Split (ISA + SIPP)",
        "alias": "p_uk_split",
    },
    "student_starter": {
        "name": "Student Starter",
        "alias": "p_student",
    },
}


def _load_json(filename: str) -> dict | list:
    filepath = _SYNTHETIC_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Synthetic data pack file {filename} not found.",
        )
    with open(filepath, "r") as f:
        return json.load(f)


def resolve_portfolio_key(portfolio_id: str) -> str:
    """Resolve canonical portfolio key from either key name or transaction portfolio_id alias."""
    raw = _load_json("portfolios.json")
    if portfolio_id in raw:
        return portfolio_id
    for key, meta in _PORTFOLIO_METADATA.items():
        if meta["alias"] == portfolio_id and key in raw:
            return key
    raise HTTPException(
        status_code=404,
        detail=f"Portfolio '{portfolio_id}' not found",
    )


def get_portfolio_name(portfolio_key: str) -> str:
    meta = _PORTFOLIO_METADATA.get(portfolio_key)
    if meta:
        return meta["name"]
    return portfolio_key.replace("_", " ").title()


def list_portfolio_keys() -> list[str]:
    raw = _load_json("portfolios.json")
    return list(raw.keys())


def build_portfolio_snapshot(portfolio_key: str) -> tuple[ValuationSnapshot, dict[str, str]]:
    """Fold ledger transactions for a synthetic portfolio into a ValuationSnapshot and ticker map."""
    raw = _load_json("portfolios.json")
    if portfolio_key not in raw:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_key}' not found")

    txs: list[dict] = raw[portfolio_key]
    base_currency = txs[0]["currency"] if txs else "EUR"

    events: list[LedgerEvent] = []
    prices: dict[str, Decimal] = {}
    tickers: dict[str, str] = {}

    for tx in txs:
        isin = tx["isin"]
        prices[isin] = Decimal(str(tx["price"]))
        if "ticker" in tx:
            tickers[isin] = tx["ticker"]
        events.append(
            LedgerEvent(
                event_id=tx["transaction_id"],
                effective_at=tx["timestamp"],
                event_type=LedgerEventType(tx["action"]),
                instrument_id=isin,
                quantity=Decimal(str(tx["shares"])),
                price=Decimal(str(tx["price"])),
                currency=tx["currency"],
                fee=Decimal(str(tx.get("fee", "0"))),
            )
        )

    res = fold_ledger(events, base_currency=base_currency, prices=prices, fx_rates={})
    if res.is_err or res.value is None:
        raise HTTPException(status_code=500, detail=f"Failed to value portfolio: {res.error}")
    return res.value, tickers


def holdings_market_value(snapshot: ValuationSnapshot) -> Decimal:
    return sum((p.market_value for p in snapshot.positions), start=Decimal("0")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def get_funds_catalog() -> dict[str, FundHoldingsDataset]:
    """Load synthetic UCITS fund holdings catalog."""
    data = _load_json("funds.json")
    catalog: dict[str, FundHoldingsDataset] = {}
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


@lru_cache(maxsize=1)
def get_synthetic_close_prices() -> dict[str, list[float]]:
    """Generate and cache deterministic daily close prices keyed by ISIN."""
    gen = SyntheticMarketGenerator(seed=42)
    companies = gen.generate_companies()
    funds = gen.generate_funds(companies)
    bars_by_isin, _ = gen.generate_prices(companies, funds)

    close_series: dict[str, list[float]] = {}
    for isin, bars in bars_by_isin.items():
        # Deduplicate multi-listing funds by date, preserving chronological order
        by_date: dict[str, float] = {}
        for bar in bars:
            if bar.date not in by_date:
                by_date[bar.date] = float(bar.close)
        close_series[isin] = list(by_date.values())
    return close_series
