# ADR-001: Product Modes and Default-Deny Data Licensing

## Status
Accepted

## Context
Waterline processes portfolio transactions, ETF fund holdings, and market prices. Financial market data and user portfolios are subject to strict licensing, privacy, and regulatory boundaries. An API key or publicly available webpage does not grant unrestricted redistribution, caching, or model training rights.

## Decision
1. **Three Isolated Operating Modes**:
   - `Synthetic Public`: Uses a deterministic fictional market with `ZZ`-prefixed ISINs. Free from copyright or privacy restrictions, used for public demos, testing, and benchmark verification.
   - `User-Authorised Private`: Operates on user-uploaded broker CSV files and holdings. Processed strictly within tenant isolation for private analytics; never repurposed for public display or model training without consent.
   - `Licensed Connected`: Governed by commercial data agreements with explicit permitted-use metadata.
2. **Default-Deny Licensing Registry**:
   All data queries verify entitlements against a license registry before access or export. Missing, expired, or non-compliant licenses trigger graceful degradation rather than unverified data distribution.
