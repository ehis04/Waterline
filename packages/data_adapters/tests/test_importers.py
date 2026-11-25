"""Tests for Trading 212 and Degiro broker CSV importers."""

from decimal import Decimal
from pathlib import Path

from data_adapters.importers import parse_degiro_csv, parse_trading212_csv

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNTHETIC_EXPORTS_DIR = REPO_ROOT / "data" / "synthetic" / "broker_exports"


def test_parse_trading212_synthetic_csv():
    csv_path = SYNTHETIC_EXPORTS_DIR / "trading212_overlapping.csv"
    result = parse_trading212_csv(csv_path.read_text(encoding="utf-8"))

    assert result.rows_read == 5
    assert result.rows_skipped == 0
    assert result.warnings == []
    assert len(result.transactions) == 5

    expected_isins = [
        "ZZET00000017",
        "ZZET00000033",
        "ZZET00000041",
        "ZZEQ01010018",
        "ZZET00000017",
    ]
    expected_totals = [
        Decimal("11775.00"),
        Decimal("8210.00"),
        Decimal("8992.00"),
        Decimal("4750.00"),
        Decimal("3368.00"),
    ]

    assert [tx.isin for tx in result.transactions] == expected_isins
    assert [tx.total for tx in result.transactions] == expected_totals
    assert [tx.external_id for tx in result.transactions] == [
        "tx_101",
        "tx_102",
        "tx_103",
        "tx_104",
        "tx_105",
    ]

    for tx in result.transactions:
        assert tx.broker == "trading212"
        assert tx.action == "BUY"
        assert tx.currency == "EUR"
        assert isinstance(tx.quantity, Decimal)
        assert isinstance(tx.price, Decimal)
        assert isinstance(tx.fee, Decimal)
        assert isinstance(tx.total, Decimal)


def test_parse_trading212_actions_and_currencies():
    content = (
        "Action,Time,ISIN,Ticker,Name,No. of shares,Price / share (USD),"
        "Currency (Price / share),Exchange rate,Result (USD),Total (USD),"
        "Withholding tax (USD),Currency conversion fee (USD),Notes\n"
        "Market sell,2024-01-10T10:00:00Z,US0378331005,AAPL,Apple,10,185.50,USD,1.00,50.00,1855.00,0.00,1.25,sell_1\n"
        "Dividend (Ordinary),2024-02-01T08:00:00Z,US0378331005,AAPL,Apple,,,USD,,,24.00,3.60,0.00,div_1\n"
        "Deposit,2024-01-01T09:00:00Z,,,,,,,,,1000.00,,,dep_1\n"
        "Withdrawal,2024-03-01T09:00:00Z,,,,,,,,,-250.00,,,wd_1\n"
    )
    result = parse_trading212_csv(content)

    assert result.rows_read == 4
    assert result.rows_skipped == 0
    assert [tx.action for tx in result.transactions] == ["SELL", "DIVIDEND", "DEPOSIT", "WITHDRAWAL"]
    assert result.transactions[0].fee == Decimal("1.25")
    assert result.transactions[1].fee == Decimal("3.60")
    assert result.transactions[2].currency == "USD"
    assert result.transactions[2].quantity == Decimal("0")
    assert result.transactions[3].total == Decimal("-250.00")


def test_parse_trading212_malformed_rows_skipped_with_warning():
    content = (
        "Action,Time,ISIN,Ticker,Name,No. of shares,Price / share (EUR),"
        "Currency (Price / share),Exchange rate,Result (EUR),Total (EUR),"
        "Withholding tax (EUR),Currency conversion fee (EUR),Notes\n"
        "Market buy,2023-01-10T09:30:00Z,ZZET00000017,PDEV,Name,10,50.00,EUR,1.00,0.00,500.00,0.00,0.00,ok_1\n"
        "Unknown action,2023-01-10T09:30:00Z,ZZET00000017,PDEV,Name,10,50.00,EUR,1.00,0.00,500.00,0.00,0.00,bad_action\n"
        "Market buy,not-a-date,ZZET00000017,PDEV,Name,10,50.00,EUR,1.00,0.00,500.00,0.00,0.00,bad_date\n"
        "Market buy,2023-01-10T09:30:00Z,ZZET00000017,PDEV,Name,10,50.00,EUR,1.00,0.00,not-a-num,0.00,0.00,bad_total\n"
    )
    result = parse_trading212_csv(content)

    assert result.rows_read == 4
    assert result.rows_skipped == 3
    assert len(result.transactions) == 1
    assert len(result.warnings) == 3
    assert result.transactions[0].external_id == "ok_1"


def test_parse_degiro_synthetic_csv():
    csv_path = SYNTHETIC_EXPORTS_DIR / "degiro_student_transactions.csv"
    result = parse_degiro_csv(csv_path.read_text(encoding="utf-8"))

    assert result.rows_read == 3
    assert result.rows_skipped == 0
    assert result.warnings == []
    assert len(result.transactions) == 3

    assert [tx.isin for tx in result.transactions] == [
        "ZZET00000017",
        "ZZET00000017",
        "ZZET00000041",
    ]
    assert [tx.total for tx in result.transactions] == [
        Decimal("-851.00"),
        Decimal("-863.00"),
        Decimal("-626.00"),
    ]
    assert [tx.external_id for tx in result.transactions] == ["tx_301", "tx_302", "tx_303"]

    for tx in result.transactions:
        assert tx.broker == "degiro"
        assert tx.action == "BUY"
        assert tx.fee == Decimal("1.00")
        assert isinstance(tx.quantity, Decimal)
        assert isinstance(tx.price, Decimal)
        assert isinstance(tx.fee, Decimal)
        assert isinstance(tx.total, Decimal)


def test_parse_degiro_european_formats_and_sell():
    content = (
        "Date;Time;Product;ISIN;Reference;Venue;Quantity;Price;Local value;Value;Exchange rate;Auto FX fee;Transaction fee;Total\n"
        "15-04-2024;09:15;Fictional PDEV;ZZET00000017;tx_sell_1;XETR;-15;1.234,50;-18.517,50;-18.517,50;1,0000;2,50;1,00;18.514,00\n"
    )
    result = parse_degiro_csv(content)

    assert result.rows_read == 1
    assert result.rows_skipped == 0
    tx = result.transactions[0]
    assert tx.timestamp == "2024-04-15T09:15:00Z"
    assert tx.action == "SELL"
    assert tx.quantity == Decimal("15")
    assert tx.price == Decimal("1234.50")
    assert tx.fee == Decimal("3.50")
    assert tx.total == Decimal("18514.00")


def test_parse_degiro_malformed_rows_skipped_with_warning():
    content = (
        "Date;Time;Product;ISIN;Reference;Venue;Quantity;Price;Local value;Value;Exchange rate;Auto FX fee;Transaction fee;Total\n"
        "2024/01/15;12:00:00;PDEV;ZZET00000017;ok_1;XETR;10;85,00;851,00;851,00;1,0000;0,00;1,00;-851,00\n"
        "invalid-date;12:00:00;PDEV;ZZET00000017;bad_1;XETR;10;85,00;851,00;851,00;1,0000;0,00;1,00;-851,00\n"
        "2024/01/15;12:00:00;PDEV;ZZET00000017;bad_2;XETR;abc;85,00;851,00;851,00;1,0000;0,00;1,00;-851,00\n"
    )
    result = parse_degiro_csv(content)

    assert result.rows_read == 3
    assert result.rows_skipped == 2
    assert len(result.transactions) == 1
    assert len(result.warnings) == 2
    assert result.transactions[0].external_id == "ok_1"


def test_empty_csv_returns_warning_without_crashing():
    t212_res = parse_trading212_csv("")
    degiro_res = parse_degiro_csv("   \n")

    assert t212_res.transactions == []
    assert len(t212_res.warnings) == 1
    assert degiro_res.transactions == []
    assert len(degiro_res.warnings) == 1
