"""Base models and shared helpers for broker CSV importers."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ParsedTransaction:
    """Normalized transaction parsed from a broker CSV export."""

    timestamp: str
    action: str
    isin: str | None
    ticker: str | None
    quantity: Decimal
    price: Decimal
    currency: str
    fee: Decimal
    total: Decimal
    external_id: str
    broker: str


@dataclass
class ImportResult:
    """Result of parsing a broker CSV export."""

    transactions: list[ParsedTransaction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows_read: int = 0
    rows_skipped: int = 0


def parse_decimal(raw: str | None, default: Decimal | None = None) -> Decimal:
    """Parse a numeric string (standard or European comma-decimal) into Decimal."""
    if raw is None:
        if default is not None:
            return default
        raise InvalidOperation("Missing numeric value")

    cleaned = raw.strip().replace("\xa0", "").replace(" ", "")
    if not cleaned:
        if default is not None:
            return default
        raise InvalidOperation("Empty numeric value")

    # European format: e.g. "1.234,56" or "85,00"
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    return Decimal(cleaned)
