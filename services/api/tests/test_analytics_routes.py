"""Integration tests for risk, scenario, and breaking-point analytics routes."""

from decimal import Decimal
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_run_risk_valid_portfolio():
    res = client.post(
        "/v1/runs/risk",
        json={"portfolio_id": "overlapping_etfs", "confidence": 0.95, "window_days": 252},
    )
    assert res.status_code == 200
    data = res.json()
    assert "var" in data
    assert "es" in data
    assert "mdd" in data
    assert "receipt_id" in data
    # Verify receipt_id is a valid UUID4
    parsed_uuid = uuid.UUID(data["receipt_id"])
    assert parsed_uuid.version == 4
    assert Decimal(data["var"]) > Decimal("0")
    assert Decimal(data["es"]) >= Decimal(data["var"])
    assert Decimal(data["mdd"]) >= Decimal("0")


def test_run_risk_unknown_portfolio_returns_404():
    res = client.post(
        "/v1/runs/risk",
        json={"portfolio_id": "unknown", "confidence": 0.95, "window_days": 252},
    )
    assert res.status_code == 404
    err = res.json()
    assert err["code"] == "HTTP_404"
    assert "request_id" in err


def test_run_scenario_stress_test():
    res = client.post(
        "/v1/runs/scenario",
        json={
            "portfolio_id": "overlapping_etfs",
            "shocks": [
                {"isin": "ZZET00000017", "override_return": -0.20},
                {"isin": "ZZET00000041", "override_return": -0.15},
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_impact" in data
    assert "receipt_id" in data
    uuid.UUID(data["receipt_id"])
    assert Decimal(data["total_impact"]) < Decimal("0")
    assert Decimal(data["loss_amount"]) > Decimal("0")
    assert len(data["position_impacts"]) == 4


def test_run_breaking_point():
    res = client.post(
        "/v1/runs/breaking-point",
        json={
            "portfolio_id": "overlapping_etfs",
            "loss_threshold": 0.15,
            "narrative": "unconstrained",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "d_star" in data
    assert "receipt_id" in data
    uuid.UUID(data["receipt_id"])
    assert data["d_star"] > 0.0
    assert "equity" in data["shocks"]


def test_run_breaking_point_unknown_portfolio_returns_404():
    res = client.post(
        "/v1/runs/breaking-point",
        json={"portfolio_id": "unknown", "loss_threshold": 0.15, "narrative": "unconstrained"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "HTTP_404"
