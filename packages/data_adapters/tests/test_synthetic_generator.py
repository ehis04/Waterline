"""Tests for synthetic market generator and ISIN validations."""

from decimal import Decimal
import csv
import io
import pytest

from data_adapters.synthetic.isin import make_isin, validate_isin, calculate_isin_check_digit
from data_adapters.synthetic.generator import SyntheticMarketGenerator
from data_adapters.synthetic.broker_exports import export_trading212_csv, export_degiro_transactions_csv


def test_isin_calculation_and_validation():
    # Known real check digits
    assert make_isin("US", "037833100") == "US0378331005"  # Apple Inc.
    assert validate_isin("US0378331005") is True
    assert validate_isin("US0378331004") is False  # Wrong check digit
    assert validate_isin("INVALID") is False


def test_synthetic_companies_spec():
    generator = SyntheticMarketGenerator(seed=42)
    companies = generator.generate_companies()

    assert len(companies) == 40
    sectors = {c.sector for c in companies}
    assert len(sectors) == 8

    # All must have ZZ country prefix and valid check digit
    for c in companies:
        assert c.isin.startswith("ZZ")
        assert validate_isin(c.isin) is True
        assert c.base_market_cap > Decimal("0")
        assert c.base_volatility > Decimal("0")


def test_synthetic_funds_constituents_sum_to_one():
    generator = SyntheticMarketGenerator(seed=42)
    companies = generator.generate_companies()
    funds = generator.generate_funds(companies)

    assert len(funds) == 8

    for f in funds:
        assert f.isin.startswith("ZZ")
        assert validate_isin(f.isin) is True
        assert len(f.listings) >= 1

        total_weight = sum(item.weight for item in f.constituents)
        assert total_weight == Decimal("1.000000"), f"Fund {f.name} constituents do not sum to 1.0"


def test_generator_determinism():
    gen1 = SyntheticMarketGenerator(seed=1234)
    pack1 = gen1.generate_all()

    gen2 = SyntheticMarketGenerator(seed=1234)
    pack2 = gen2.generate_all()

    assert len(pack1.companies) == len(pack2.companies)
    for c1, c2 in zip(pack1.companies, pack2.companies):
        assert c1 == c2


def test_broker_csv_exports():
    generator = SyntheticMarketGenerator(seed=42)
    companies = generator.generate_companies()
    funds = generator.generate_funds(companies)
    portfolios = generator.generate_demo_portfolios(companies, funds)

    t212_csv = export_trading212_csv(portfolios["overlapping_etfs"])
    reader = csv.reader(io.StringIO(t212_csv))
    rows = list(reader)
    assert len(rows) == len(portfolios["overlapping_etfs"]) + 1
    assert "Action" in rows[0][0]

    degiro_csv = export_degiro_transactions_csv(portfolios["student_starter"])
    reader_degiro = csv.reader(io.StringIO(degiro_csv), delimiter=";")
    rows_degiro = list(reader_degiro)
    assert len(rows_degiro) == len(portfolios["student_starter"]) + 1
