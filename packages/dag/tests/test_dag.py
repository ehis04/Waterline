"""Tests for RFC 8785 canonical serialization, DAG execution, caching, and cycle detection."""

import pytest
from dag.canonical import canonical_json, canonical_hash
from dag.node import DAGNode
from dag.executor import DAGExecutor, NodeCache


def test_canonical_json_key_ordering():
    # In RFC 8785, keys must be ordered lexicographically by Unicode code point
    dict_unordered = {"zebra": 1, "apple": 2, "mango": 3}
    serialized = canonical_json(dict_unordered)
    assert serialized == '{"apple":2,"mango":3,"zebra":1}'


def test_content_addressed_node_id_stability():
    n1 = DAGNode(fn="test.fn", version="1.0", params={"a": 10, "b": "val"})
    n2 = DAGNode(fn="test.fn", version="1.0", params={"b": "val", "a": 10})
    assert n1.node_id == n2.node_id
    assert n1.node_id.startswith("n_")


def test_dag_cycle_detection():
    # Direct cyclic dependency: A -> B and B -> A
    n1 = DAGNode(fn="step_a", version="1.0", inputs=["node_b"], node_id_override="node_a")
    n2 = DAGNode(fn="step_b", version="1.0", inputs=["node_a"], node_id_override="node_b")

    executor = DAGExecutor()
    with pytest.raises(ValueError, match="Cycle detected"):
        executor.topological_sort([n1, n2])


def test_dag_execution_and_caching():
    executor = DAGExecutor()
    eval_count = 0

    @executor.register("math.add", "1.0")
    def add(x: int, y: int) -> int:
        nonlocal eval_count
        eval_count += 1
        return x + y

    n1 = DAGNode(fn="math.add", version="1.0", params={"x": 5, "y": 7})
    nodes = [n1]

    # First run: evaluated
    res1 = executor.execute(nodes)
    assert res1[n1.node_id] == 12
    assert eval_count == 1

    # Second run: cache hit
    res2 = executor.execute(nodes)
    assert res2[n1.node_id] == 12
    assert eval_count == 1  # Not incremented due to cache
