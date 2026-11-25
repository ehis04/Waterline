# Waterline

Open-core portfolio risk workbench for ETF and multi-asset investors.

## Overview

Waterline provides look-through exposure analysis, stress testing, reverse stress testing, and risk attribution with verifiable calculation receipts.

### Architecture

- `packages/risk_core`: Pure quantitative risk library (accounting, valuation, returns, VaR/ES, stress).
- `packages/dag`: Deterministic computation DAG executor and cryptographic receipt generator.
- `packages/lookthrough`: Constituent expansion, entity resolution, and ETF overlap calculation.
- `packages/data_adapters`: Provider-neutral market data and reference data adapters.
- `services/api`: FastAPI application serving portfolio and analytics endpoints.
- `services/worker`: Background task worker for analytical jobs and cache precomputation.
- `apps/web`: Next.js web application.

## Development

```bash
# Python workspace
uv venv
uv pip install -e "packages/risk_core"

# Test suite
pytest
```
