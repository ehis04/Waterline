#!/usr/bin/env python3
"""CLI script to generate deterministic synthetic market dataset and broker files."""

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

# Ensure data_adapters package is on path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "packages" / "data_adapters" / "src"))

from data_adapters.synthetic.generator import SyntheticMarketGenerator
from data_adapters.synthetic.broker_exports import export_trading212_csv, export_degiro_transactions_csv


def decimal_serializer(obj):
    from decimal import Decimal
    from enum import Enum
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    print("Generating synthetic market pack (seed=42)...")
    generator = SyntheticMarketGenerator(seed=42)
    pack = generator.generate_all()

    out_dir = repo_root / "data" / "synthetic"
    broker_dir = out_dir / "broker_exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    broker_dir.mkdir(parents=True, exist_ok=True)

    # 1. Companies
    companies_file = out_dir / "companies.json"
    with open(companies_file, "w") as f:
        json.dump([asdict(c) for c in pack.companies], f, indent=2, default=decimal_serializer)

    # 2. Funds
    funds_file = out_dir / "funds.json"
    with open(funds_file, "w") as f:
        json.dump([asdict(fd) for fd in pack.funds], f, indent=2, default=decimal_serializer)

    # 3. Corporate Actions
    actions_file = out_dir / "corporate_actions.json"
    with open(actions_file, "w") as f:
        json.dump([asdict(a) for a in pack.corporate_actions], f, indent=2, default=decimal_serializer)

    # 4. Portfolios
    portfolios_file = out_dir / "portfolios.json"
    with open(portfolios_file, "w") as f:
        json.dump(
            {k: [asdict(t) for t in txs] for k, txs in pack.portfolios.items()},
            f,
            indent=2,
            default=decimal_serializer,
        )

    # 5. Broker Exports
    t212_file = broker_dir / "trading212_overlapping.csv"
    with open(t212_file, "w") as f:
        f.write(export_trading212_csv(pack.portfolios["overlapping_etfs"]))

    degiro_file = broker_dir / "degiro_student_transactions.csv"
    with open(degiro_file, "w") as f:
        f.write(export_degiro_transactions_csv(pack.portfolios["student_starter"]))

    # 6. Manifest
    manifest = {
        "version": pack.version,
        "seed": pack.seed,
        "companies_count": len(pack.companies),
        "funds_count": len(pack.funds),
        "portfolios_count": len(pack.portfolios),
        "files": {
            "companies.json": compute_sha256(companies_file),
            "funds.json": compute_sha256(funds_file),
            "corporate_actions.json": compute_sha256(actions_file),
            "portfolios.json": compute_sha256(portfolios_file),
            "trading212_overlapping.csv": compute_sha256(t212_file),
            "degiro_student_transactions.csv": compute_sha256(degiro_file),
        },
    }

    manifest_file = out_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated synthetic pack successfully at {out_dir}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
