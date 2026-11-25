"""Content-addressed computation DAG node definition."""

from dataclasses import dataclass, field
from typing import Any
from dag.canonical import canonical_hash


@dataclass(frozen=True)
class DAGNode:
    fn: str
    version: str
    params: dict[str, Any] = field(default_factory=dict)
    inputs: list[str] = field(default_factory=list)
    input_datasets: list[str] = field(default_factory=list)
    node_id_override: str | None = None

    @property
    def node_id(self) -> str:
        """Content-addressed SHA-256 node identifier."""
        if self.node_id_override:
            return self.node_id_override
        spec = {
            "fn": self.fn,
            "version": self.version,
            "params": self.params,
            "inputs": self.inputs,
            "input_datasets": self.input_datasets,
        }
        digest = canonical_hash(spec)
        return f"n_{digest[:16]}"
