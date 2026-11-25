"""Contract and integration tests for FastAPI service."""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from dag.node import DAGNode
from dag.receipt import build_receipt_v2

client = TestClient(app)


def test_health_live_and_ready():
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "live"
    assert "X-Request-ID" in res_live.headers

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_demo_portfolios_endpoint():
    res = client.get("/v1/demo/portfolios")
    assert res.status_code == 200
    data = res.json()
    assert "overlapping_etfs" in data
    assert "uk_wrapper_split" in data
    assert "student_starter" in data


def test_public_overlap_endpoint():
    # Funds from synthetic universe:
    # ZZET00000017: Global Core
    # ZZET00000041: Tech Titans
    res = client.get("/v1/public/overlap?isins=ZZET00000017,ZZET00000041")
    assert res.status_code == 200
    data = res.json()
    assert len(data["pairwise"]) == 1
    item = data["pairwise"][0]
    assert item["weight_overlap"] > 0.0
    assert item["common_entities_count"] > 0


def test_public_overlap_missing_isin_error_contract():
    res = client.get("/v1/public/overlap?isins=ZZET00000017,ZZ9999999999")
    assert res.status_code == 404
    error = res.json()
    assert error["code"] == "HTTP_404"
    assert "not found" in error["message"].lower()
    assert "request_id" in error


def test_receipt_verify_endpoint():
    node = DAGNode(fn="test.fn", version="1.0")
    receipt = build_receipt_v2(
        run_id="run_test_001",
        run_type="test_run",
        statement_type="scenario",
        as_of="2026-11-25T12:00:00Z",
        knowledge_time="2026-11-25T12:00:00Z",
        mode="synthetic_demo",
        base_currency="EUR",
        portfolio_snapshot={"id": "snap_1", "content_sha256": "abc"},
        inputs=[],
        nodes=[node],
        root_node_id=node.node_id,
        result={"val": 100},
        coverage={"priced_weight": 1.0},
    )

    # 1. Valid receipt
    res_valid = client.post("/v1/receipts/verify", json={"receipt": receipt})
    assert res_valid.status_code == 200
    assert res_valid.json()["valid"] is True

    # 2. Tampered receipt
    tampered = dict(receipt)
    tampered["result"] = {"val": 999}
    res_tampered = client.post("/v1/receipts/verify", json={"receipt": tampered})
    assert res_tampered.status_code == 200
    assert res_tampered.json()["valid"] is False
    assert "Hash mismatch" in res_tampered.json()["reason"]
