"""Deterministic computation DAG and calculation receipt builder."""

from dag.canonical import canonical_json, canonical_hash
from dag.node import DAGNode
from dag.executor import DAGExecutor, NodeCache
from dag.receipt import build_receipt_v2, verify_receipt_integrity

__version__ = "0.1.0"

__all__ = [
    "canonical_json",
    "canonical_hash",
    "DAGNode",
    "DAGExecutor",
    "NodeCache",
    "build_receipt_v2",
    "verify_receipt_integrity",
]
