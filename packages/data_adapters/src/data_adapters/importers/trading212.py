"""Trading 212 CSV export parser."""

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from data_adapters.importers.base import ImportResult, ParsedTransaction, parse_decimal

_ACTION_MAP: dict[str, str] = {
    "market buy": "BUY",
    "limit buy": "BUY",
    "stop buy": "BUY",
    "market sell": "SELL",
    "limit sell": "SELL",
    "stop sell": "SELL",
    "dividend": "DIVIDEND",
    "deposit": "DEPOSIT",
    "withdrawal": "WITHDRAWAL",
}


def _find_column(fieldnames: list[str], prefix: str) -> str | None:
    """Find the first column matching a prefix (handles currency suffixes like 'Total (EUR)')."""
    prefix_lower = prefix.lower()
    for name in fieldnames:
        if name.strip().lower().startswith(prefix_lower):
            return name
    return None


def _extract_currency_from_header(col_name: str | None) -> str | None:
    """Extract currency code from a header like 'Total (EUR)'."""
    if not col_name:
        return None
    match = re.search(r"\(([A-Z]{3})\)", col_name)
    return match.group(1) if match else None


def _normalize_action(raw_action: str) -> str | None:
    """Map Trading 212 action labels to normalized action strings."""
    key = raw_action.strip().lower()
    if key in _ACTION_MAP:
        return _ACTION_MAP[key]
    if key.startswith("dividend"):
        return "DIVIDEND"
    return None


def _validate_iso_timestamp(raw_ts: str) -> str:
    """Validate an ISO 8601 timestamp string and return it normalized."""
    ts = raw_ts.strip()
    if not ts:
        raise ValueError("Empty timestamp")
    datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return ts


def parse_trading212_csv(content: str) -> ImportResult:
    """Parse a Trading 212 CSV export into normalized transactions."""
    result = ImportResult()
    if not content or not content.strip():
        result.warnings.append("Empty Trading 212 CSV content")
        return result

    reader = csv.DictReader(io.StringIO(content.strip()))
    if not reader.fieldnames:
        result.warnings.append("Missing CSV header row")
        return result

    fieldnames = list(reader.fieldnames)
    price_col = _find_column(fieldnames, "Price / share")
    total_col = _find_column(fieldnames, "Total")
    fx_fee_col = _find_column(fieldnames, "Currency conversion fee")
    tax_col = _find_column(fieldnames, "Withholding tax")
    account_currency = _extract_currency_from_header(total_col) or "EUR"

    if "Action" not in fieldnames or "Time" not in fieldnames or not total_col:
        result.warnings.append("Missing required Trading 212 columns (Action, Time, Total)")
        return result

    for row_idx, row in enumerate(reader, start=2):
        result.rows_read += 1
        try:
            action = _normalize_action(row.get("Action") or "")
            if not action:
                raise ValueError(f"Unsupported action: {row.get('Action')!r}")

            timestamp = _validate_iso_timestamp(row.get("Time") or "")
            isin = (row.get("ISIN") or "").strip() or None
            ticker = (row.get("Ticker") or "").strip() or None

            quantity = parse_decimal(row.get("No. of shares"), default=Decimal("0"))
            price = parse_decimal(row.get(price_col) if price_col else None, default=Decimal("0"))
            total = parse_decimal(row.get(total_col))

            fx_fee = parse_decimal(row.get(fx_fee_col) if fx_fee_col else None, default=Decimal("0"))
            withholding_tax = parse_decimal(row.get(tax_col) if tax_col else None, default=Decimal("0"))
            fee = fx_fee + withholding_tax

            currency = (row.get("Currency (Price / share)") or "").strip() or account_currency

            notes = (row.get("Notes") or "").strip()
            if notes.startswith("Ref "):
                external_id = notes[4:].strip()
            elif notes:
                external_id = notes
            else:
                external_id = f"t212_row_{row_idx}"

            result.transactions.append(
                ParsedTransaction(
                    timestamp=timestamp,
                    action=action,
                    isin=isin,
                    ticker=ticker,
                    quantity=quantity,
                    price=price,
                    currency=currency,
                    fee=fee,
                    total=total,
                    external_id=external_id,
                    broker="trading212",
                )
            )
        except (ValueError, InvalidOperation, KeyError) as exc:
            result.rows_skipped += 1
            result.warnings.append(f"Row {row_idx}: {exc}")

    return result
