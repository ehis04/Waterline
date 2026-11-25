# Waterline Threat Model v1 (STRIDE)

## Scope & Trust Boundaries

Waterline is an open-core portfolio risk workbench with a Next.js web client (`apps/web`), a FastAPI service (`services/api`), pure analytical libraries (`packages/risk_core`, `packages/lookthrough`, `packages/dag`), and PostgreSQL persistence (`infra/compose/docker-compose.yml`).

Primary trust boundaries:
1. **Client -> API**: Untrusted HTTP requests, tenant headers (`X-Tenant-ID`), and broker CSV uploads.
2. **API -> Market Data / Licensing**: Separation between `Synthetic Public`, `User-Authorised Private`, and `Licensed Connected` operating modes (per `ADR-001`).
3. **API -> Receipt Verifier**: Cryptographic verification of computation receipts (`ADR-004`).
4. **Application -> Logs / Telemetry**: Structured logging pipeline emitting operational diagnostics.

---

## STRIDE Threat Analysis

| Area | STRIDE Category | Threat Description | Impact | Mitigation | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Multi-Tenant Portfolio Isolation** | **I**nformation Disclosure / **E**levation of Privilege / **S**poofing | A caller supplies a forged or mismatched `X-Tenant-ID` header or guesses another tenant's `portfolio_id` (IDOR) to read holdings, X-Ray exposures, or run risk/scenario analytics on another tenant's portfolio. | Cross-tenant leakage of private portfolio positions and valuations. | Enforce `get_tenant_id` validation and `verify_portfolio_tenant_access` on all `/v1/portfolios*` and `/v1/runs*` endpoints; filter portfolio listings by tenant; return `403` `ErrorResponse` without leaking target holdings. | `services/api/tests/test_security.py` cross-tenant isolation harness. |
| **2. Broker CSV Upload Parsing** | **T**ampering / **D**enial of Service | Malicious broker CSVs contain spreadsheet formula payloads (`=`, `+`, `-`, `@`, `\t`, `\r`) that execute on re-export (CSV injection), or malformed decimals (`NaN`, `Inf`, non-numeric strings) that corrupt ledger folding. | Client-side code execution in Excel/Sheets; unhandled exceptions or corrupted `Decimal` valuations. | Sanitize exported/echoed CSV cells via `sanitize_csv_cell` (prefixing `'`); parse monetary quantities strictly with `Decimal` and reject `NaN`/`Infinity` and non-finite inputs at schema/adapter boundaries. | `services/api/tests/test_security.py` CSV formula injection tests; `risk_core` accounting validation. |
| **3. Receipt Tamper Verification** | **T**ampering / **R**epudiation | An attacker or faulty intermediary modifies a calculation receipt's `result`, `inputs`, or `nodes` after execution to misrepresent VaR, ES, or stress-test outcomes. | Undetected manipulation of auditable risk figures. | Serialize receipts using RFC 8785 Canonical JSON and compute `integrity.receipt_sha256`; verify via `/v1/receipts/verify` (`verify_receipt_integrity`) before trusting any receipt. | `services/api/tests/test_api_contracts.py::test_receipt_verify_endpoint` and `packages/dag/tests/test_golden_receipt.py`. |
| **4. Third-Party Market Data Licence Boundaries** | **I**nformation Disclosure / **E**levation of Privilege | Commercial or user-private holdings/prices leak into `Synthetic Public` demo endpoints or unauthorized exports, violating data provider redistribution licences. | Contractual/regulatory breach and unauthorized data redistribution. | Enforce `ADR-001` mode isolation (`ZZ`-prefixed synthetic ISINs for public demos) and default-deny licensing registry checks before data access or export. | `scripts/verify_synthetic_manifest.py` integrity check in CI; `ADR-001` boundary reviews. |
| **5. Log & Telemetry PII Redaction** | **I**nformation Disclosure | Structured or freeform logs accidentally record `Authorization` headers, `api_key`, `token`, `email`, or `account_number` fields in stdout, log files, or error traces. | Credential compromise and PII exposure in log aggregators. | Attach `RedactingFilter` (`services/api/app/logging_utils.py`) to application loggers and use `redact_sensitive_data` / `redact_text` to replace sensitive values with `[REDACTED]`. | `services/api/tests/test_security.py` log redaction suite. |
