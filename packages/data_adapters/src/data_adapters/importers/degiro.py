"""Degiro CSV transaction export parser."""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from data_adapters.importers.base import ImportResult, ParsedTransaction, parse_decimal

_DATE_FORMATS = ("%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y")
_TIME_FORMATS = ("%H:%M:%S", "%H:%M")


def _parse_degiro_timestamp(date_raw: str, time_raw: str) -> str:
    """Parse Degiro Date and Time columns into an ISO 8601 UTC timestamp string."""
    date_str = date_raw.strip()
    time_str = time_raw.strip() or "00:00:00"
    if not date_str:
        raise ValueError("Empty date")

    parsed_date = None
    for fmt in _DATE_FORMATS:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue
    if parsed_date is None:
        raise ValueError(f"Unrecognized date format: {date_str!r}")

    parsed_time = None
    for fmt in _TIME_FORMATS:
        try:
            parsed_time = datetime.strptime(time_str, fmt).time()
            break
        except ValueError:
            continue
    if parsed_time is None:
        raise ValueError(f"Unrecognized time format: {time_str!r}")

    return datetime.combine(parsed_date, parsed_time).strftime("%Y-%m-%dT%H:%M:%SZ")


def _detect_delimiter(content: str) -> str:
    """Detect semicolon vs comma delimiter from the header line."""
    first_line = content.lstrip().splitlines()[0]
    return ";" if first_line.count(";") >= first_line.count(",") else ","


def parse_degiro_csv(content: str) -> ImportResult:
    """Parse a Degiro Transactions CSV export into normalized transactions."""
    result = ImportResult()
    if not content or not content.strip():
        result.warnings.append("Empty Degiro CSV content")
        return result

    delimiter = _detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content.strip()), delimiter=delimiter)
    if not reader.fieldnames:
        result.warnings.append("Missing CSV header row")
        return result

    fieldnames = set(reader.fieldnames)
    required = {"Date", "Time", "Quantity", "Price", "Total"}
    if not required.issubset(fieldnames):
        missing = sorted(required - fieldnames)
        result.warnings.append(f"Missing required Degiro columns: {', '.join(missing)}")
        return result

    for row_idx, row in enumerate(reader, start=2):
        result.rows_read += 1
        try:
            timestamp = _parse_degiro_timestamp(row.get("Date") or "", row.get("Time") or "")
            raw_qty = parse_decimal(row.get("Quantity"))
            action = "BUY" if raw_qty >= 0 else "SELL"
            quantity = abs(raw_qty)

            price = parse_decimal(row.get("Price"))
            total = parse_decimal(row.get("Total"))
            fx_fee = parse_decimal(row.get("Auto FX fee"), default=Decimal("0"))
            tx_fee = parse_decimal(row.get("Transaction fee"), default=Decimal("0"))
            fee = fx_fee + tx_fee

            isin = (row.get("ISIN") or "").strip() or None
            ticker = (row.get("Ticker") or "").strip() or None
            currency = (row.get("Currency") or "").strip() or "EUR"
            external_id = (row.get("Reference") or "").strip() or f"degiro_row_{row_idx}"

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
                    broker="degiro",
                )
            )
        except (ValueError, InvalidOperation, KeyError) as exc:
            result.rows_skipped += 1
            result.warnings.append(f"Row {row_idx}: {exc}")

    return result
