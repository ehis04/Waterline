"""Integration tests for portfolio CRUD and look-through X-Ray routes."""

from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_portfolios():
    res = client.get("/v1/portfolios")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "portfolio_id" in first
    assert "base_currency" in first
    assert Decimal(first["total_market_value"]) > Decimal("0")


def test_get_portfolio_detail():
    res = client.get("/v1/portfolios/overlapping_etfs")
    assert res.status_code == 200
    data = res.json()
    assert data["portfolio_id"] == "overlapping_etfs"
    assert data["base_currency"] == "EUR"
    assert len(data["positions"]) == 4
    for pos in data["positions"]:
        assert Decimal(pos["market_value"]) > Decimal("0")
        assert Decimal(pos["weight"]) > Decimal("0")


def test_get_portfolio_unknown_returns_404_error_response():
    res = client.get("/v1/portfolios/unknown")
    assert res.status_code == 404
    err = res.json()
    assert err["code"] == "HTTP_404"
    assert "not found" in err["message"].lower()
    assert "request_id" in err


def test_get_portfolio_xray():
    res = client.get("/v1/portfolios/overlapping_etfs/xray")
    assert res.status_code == 200
    data = res.json()
    assert data["portfolio_id"] == "overlapping_etfs"
    assert isinstance(data["positions"], list)
    assert len(data["positions"]) > 0
    total_weight = sum(Decimal(p["weight"]) for p in data["positions"])
    assert total_weight > Decimal("0.9")


def test_get_portfolio_xray_unknown_returns_404():
    res = client.get("/v1/portfolios/unknown/xray")
    assert res.status_code == 404
    err = res.json()
    assert err["code"] == "HTTP_404"
