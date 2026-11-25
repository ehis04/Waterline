#!/usr/bin/env python3
"""Verify SHA-256 digests in data/synthetic/manifest.json against files on disk."""

import hashlib
import json
from pathlib import Path
import sys


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    synthetic_dir = repo_root / "data" / "synthetic"
    manifest_path = synthetic_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: Missing manifest at {manifest_path}", file=sys.stderr)
        return 1

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    files: dict[str, str] = manifest.get("files", {})
    if not files:
        print("ERROR: Manifest contains no file entries", file=sys.stderr)
        return 1

    failures = 0
    for filename, expected_sha in files.items():
        candidate = synthetic_dir / filename
        if not candidate.exists() and filename.endswith(".csv"):
            candidate = synthetic_dir / "broker_exports" / filename

        if not candidate.exists():
            print(f"MISSING: {filename}", file=sys.stderr)
            failures += 1
            continue

        actual_sha = compute_sha256(candidate)
        if actual_sha != expected_sha:
            print(
                f"MISMATCH: {filename} expected={expected_sha} actual={actual_sha}",
                file=sys.stderr,
            )
            failures += 1
        else:
            print(f"OK: {filename} ({actual_sha[:12]}...)")

    if failures:
        print(f"Verification failed with {failures} error(s).", file=sys.stderr)
        return 1

    print(f"All {len(files)} synthetic data manifest hashes verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
