"""RFC 8785 JSON Canonicalization Scheme (JCS) serializer and SHA-256 hashing."""

from decimal import Decimal
import hashlib
import json
import math
from typing import Any


def canonical_json(data: Any) -> str:
    """Serialize data into a deterministic canonical JSON string per RFC 8785."""
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "true" if data else "false"
    if isinstance(data, int):
        return str(data)
    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            raise ValueError(f"Cannot canonically serialize non-finite float: {data}")
        # RFC 8785 number formatting
        if data == 0.0:
            return "0"
        s = repr(data)
        # Handle cases where repr might have positive exponent '+' or trailing '.0'
        return s
    if isinstance(data, Decimal):
        # Format Decimal without exponential notation if feasible or exact string
        return json.dumps(str(data))
    if isinstance(data, str):
        return json.dumps(data)
    if isinstance(data, (list, tuple)):
        items = [canonical_json(item) for item in data]
        return f"[{','.join(items)}]"
    if isinstance(data, dict):
        # Sort keys lexicographically by Unicode code points
        sorted_keys = sorted(data.keys())
        entries = []
        for k in sorted_keys:
            key_str = json.dumps(str(k))
            val_str = canonical_json(data[k])
            entries.append(f"{key_str}:{val_str}")
        return f"{{{','.join(entries)}}}"

    # Handle dataclasses or objects with __dict__
    if hasattr(data, "__dict__"):
        return canonical_json(vars(data))

    raise TypeError(f"Unsupported data type for canonical serialization: {type(data)}")


def canonical_hash(data: Any) -> str:
    """Compute the SHA-256 digest of canonicalized JSON representation."""
    canonical_bytes = canonical_json(data).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()
