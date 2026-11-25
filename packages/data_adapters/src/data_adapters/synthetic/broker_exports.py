"""Generates messy broker CSV exports (Trading 212 and Degiro formats) for synthetic portfolios."""

import csv
import io
from data_adapters.synthetic.models import PortfolioTransaction


def export_trading212_csv(transactions: list[PortfolioTransaction], account_currency: str = "EUR") -> str:
    """Export transactions in Trading 212 History CSV export format."""
    out = io.StringIO()
    writer = csv.writer(out)

    # Trading 212 format headers with account currency suffix
    headers = [
        "Action",
        "Time",
        "ISIN",
        "Ticker",
        "Name",
        "No. of shares",
        f"Price / share ({account_currency})",
        "Currency (Price / share)",
        "Exchange rate",
        f"Result ({account_currency})",
        f"Total ({account_currency})",
        f"Withholding tax ({account_currency})",
        f"Currency conversion fee ({account_currency})",
        "Notes",
    ]
    writer.writerow(headers)

    for tx in transactions:
        action_str = "Market buy" if tx.action.value == "BUY" else "Market sell"
        row = [
            action_str,
            tx.timestamp,
            tx.isin or "",
            tx.ticker or "",
            f"Fictional Security {tx.ticker}",
            str(tx.shares),
            str(tx.price),
            tx.currency,
            "1.00" if tx.currency == account_currency else "1.15",
            "0.00",
            str(tx.total_amount),
            "0.00",
            str(tx.fee),
            f"Ref {tx.transaction_id}",
        ]
        writer.writerow(row)

    return out.getvalue()


def export_degiro_transactions_csv(transactions: list[PortfolioTransaction]) -> str:
    """Export trades in Degiro Transactions.csv format (semicolon delimited)."""
    out = io.StringIO()
    # Degiro EU exports typically use semicolon delimiter
    writer = csv.writer(out, delimiter=";")

    headers = [
        "Date",
        "Time",
        "Product",
        "ISIN",
        "Reference",
        "Venue",
        "Quantity",
        "Price",
        "Local value",
        "Value",
        "Exchange rate",
        "Auto FX fee",
        "Transaction fee",
        "Total",
    ]
    writer.writerow(headers)

    for tx in transactions:
        dt_part = tx.timestamp.split("T")
        date_str = dt_part[0].replace("-", "/")
        time_str = dt_part[1].replace("Z", "") if len(dt_part) > 1 else "10:00"
        qty = str(tx.shares if tx.action.value == "BUY" else -tx.shares)

        row = [
            date_str,
            time_str,
            f"Fictional {tx.ticker}",
            tx.isin or "",
            tx.transaction_id,
            "XETR",
            qty,
            str(tx.price).replace(".", ","),
            str(tx.total_amount).replace(".", ","),
            str(tx.total_amount).replace(".", ","),
            "1,0000",
            "0,00",
            str(tx.fee).replace(".", ","),
            str(-tx.total_amount).replace(".", ","),
        ]
        writer.writerow(row)

    return out.getvalue()
