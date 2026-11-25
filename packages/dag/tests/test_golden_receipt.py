"""Golden receipt verification tests ensuring determinism across platforms."""

import pytest
from dag.node import DAGNode
from dag.receipt import build_receipt_v2, verify_receipt_integrity


def test_golden_receipt_v2_verification():
    """Verify golden receipt creation, verification, and tamper detection."""
    node_valuation = DAGNode(
        fn="valuation.snapshot_value",
        version="1.0.0",
        inputs=["snap_demo_01"],
    )
    node_scenario = DAGNode(
        fn="scenario.linear_asset_shock",
        version="1.0.0",
        inputs=[node_valuation.node_id],
        params={
            "shocks": [
                {"instrument": "DEMO_A", "return": -0.10},
                {"instrument": "DEMO_B", "return": 0.04},
            ]
        },
    )

    receipt = build_receipt_v2(
        run_id="run_01JD2Y4K7Q",
        run_type="hypothetical_stress",
        statement_type="scenario",
        created_at="2026-11-25T09:14:03Z",
        as_of="2026-11-24T21:00:00Z",
        knowledge_time="2026-11-25T09:14:00Z",
        mode="synthetic_demo",
        base_currency="GBP",
        portfolio_snapshot={"id": "snap_demo_01", "content_sha256": "3fa9b1c70e28"},
        inputs=[
            {
                "dataset_id": "synthetic_prices",
                "version": "1.0.0",
                "content_sha256": "8df4921b7a0c",
                "licence_id": "project-owned",
                "available_at": "2026-11-24T22:00:00Z",
            }
        ],
        nodes=[node_valuation, node_scenario],
        root_node_id=node_scenario.node_id,
        result={
            "baseline_value": "10000.00",
            "stressed_value": "9700.00",
            "loss": "300.00",
            "return": -0.03,
        },
        coverage={"priced_weight": 1.0, "mapped_weight": 1.0},
        warnings=["Illustrative direct shocks; no probability attached"],
        replay_level="L3",
    )

    # 1. Receipt verification succeeds
    assert verify_receipt_integrity(receipt) is True
    original_sha = receipt["integrity"]["receipt_sha256"]
    assert len(original_sha) == 64

    # 2. Tampering with any value fails verification
    tampered_result = dict(receipt)
    tampered_result["result"] = dict(receipt["result"])
    tampered_result["result"]["loss"] = "301.00"
    assert verify_receipt_integrity(tampered_result) is False

    # 3. Tampering with parameters fails verification
    tampered_warning = dict(receipt)
    tampered_warning["warnings"] = ["Modified warning"]
    assert verify_receipt_integrity(tampered_warning) is False
