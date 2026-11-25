"""Receipt Schema v2.0 generation, canonicalization, and cryptographic verification."""

from dataclasses import asdict
from datetime import datetime, timezone
import copy
from typing import Any

from dag.canonical import canonical_hash, canonical_json
from dag.node import DAGNode


def build_receipt_v2(
    run_id: str,
    run_type: str,
    statement_type: str,
    as_of: str,
    knowledge_time: str,
    mode: str,
    base_currency: str,
    portfolio_snapshot: dict[str, str],
    inputs: list[dict[str, Any]],
    nodes: list[DAGNode],
    root_node_id: str,
    result: dict[str, Any],
    coverage: dict[str, Any],
    warnings: list[str] | None = None,
    seed: int | None = None,
    replay_level: str = "L3",
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build and seal a verifiable Receipt Schema v2.0 document."""
    timestamp = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    node_specs = []
    for n in nodes:
        spec = {
            "id": n.node_id,
            "fn": n.fn,
            "version": n.version,
            "inputs": n.inputs,
        }
        if n.params:
            spec["params"] = n.params
        node_specs.append(spec)

    receipt = {
        "schema_version": "2.0",
        "run_id": run_id,
        "run_type": run_type,
        "statement_type": statement_type,
        "created_at": timestamp,
        "as_of": as_of,
        "knowledge_time": knowledge_time,
        "mode": mode,
        "base_currency": base_currency,
        "portfolio_snapshot": portfolio_snapshot,
        "inputs": inputs,
        "dag": {
            "root": root_node_id,
            "nodes": node_specs,
        },
        "environment": {
            "risk_core": "0.1.0",
            "python": "3.12",
            "numpy": "2.0",
            "lockfile_sha256": "deterministic_dev_lock",
        },
        "seed": seed,
        "result": result,
        "coverage": coverage,
        "warnings": warnings or [],
        "parent_run_id": None,
        "replay_level": replay_level,
        "integrity": {
            "canonicalisation": "RFC8785",
            "hash_alg": "SHA-256",
            "receipt_sha256": "",
            "signature": None,
        },
    }

    # Seal receipt: hash the canonical JSON of receipt with empty receipt_sha256 and null signature
    pre_seal = copy.deepcopy(receipt)
    pre_seal["integrity"]["receipt_sha256"] = ""
    pre_seal["integrity"]["signature"] = None
    digest = canonical_hash(pre_seal)

    receipt["integrity"]["receipt_sha256"] = digest
    return receipt


def verify_receipt_integrity(receipt: dict[str, Any]) -> bool:
    """Verify that the receipt_sha256 matches the RFC 8785 canonical hash of the receipt content."""
    integrity = receipt.get("integrity", {})
    recorded_hash = integrity.get("receipt_sha256")
    if not recorded_hash:
        return False

    verify_copy = copy.deepcopy(receipt)
    verify_copy["integrity"]["receipt_sha256"] = ""
    verify_copy["integrity"]["signature"] = None

    computed_hash = canonical_hash(verify_copy)
    return computed_hash == recorded_hash
