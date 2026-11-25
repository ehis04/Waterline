"""Deterministic DAG execution engine with caching and cycle detection."""

from collections import defaultdict, deque
from typing import Any, Callable
from dag.node import DAGNode


class NodeCache:
    """In-memory key-value cache for content-addressed node evaluations."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, node_id: str) -> Any | None:
        return self._store.get(node_id)

    def set(self, node_id: str, value: Any) -> None:
        self._store[node_id] = value

    def contains(self, node_id: str) -> bool:
        return node_id in self._store


class DAGExecutor:
    """Executes a directed acyclic graph of pure quantitative functions."""

    def __init__(self, cache: NodeCache | None = None) -> None:
        self.cache = cache or NodeCache()
        self._registry: dict[tuple[str, str], Callable[..., Any]] = {}

    def register(self, fn: str, version: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a pure function by name and version."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._registry[(fn, version)] = func
            return func
        return decorator

    def topological_sort(self, nodes: list[DAGNode]) -> list[DAGNode]:
        """Order nodes topologically; raise ValueError on cycle detection."""
        node_map = {n.node_id: n for n in nodes}
        in_degree: dict[str, int] = {n.node_id: 0 for n in nodes}
        graph: dict[str, list[str]] = defaultdict(list)

        for n in nodes:
            for parent_id in n.inputs:
                if parent_id in node_map:
                    graph[parent_id].append(n.node_id)
                    in_degree[n.node_id] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        sorted_nodes: list[DAGNode] = []

        while queue:
            curr_id = queue.popleft()
            sorted_nodes.append(node_map[curr_id])
            for child_id in graph[curr_id]:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        if len(sorted_nodes) != len(nodes):
            raise ValueError("Cycle detected in computation DAG")

        return sorted_nodes

    def execute(
        self,
        nodes: list[DAGNode],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute all nodes in topological order and return map of {node_id: result}."""
        sorted_nodes = self.topological_sort(nodes)
        results: dict[str, Any] = dict(context or {})

        for node in sorted_nodes:
            nid = node.node_id
            if self.cache.contains(nid):
                results[nid] = self.cache.get(nid)
                continue

            key = (node.fn, node.version)
            if key not in self._registry:
                raise KeyError(f"Function '{node.fn}' version '{node.version}' is not registered in executor")

            func = self._registry[key]
            # Gather inputs from parent node outputs
            parent_outputs = [results[pid] for pid in node.inputs if pid in results]
            
            # Call pure function with parent outputs and keyword params
            res = func(*parent_outputs, **node.params)
            self.cache.set(nid, res)
            results[nid] = res

        return results
