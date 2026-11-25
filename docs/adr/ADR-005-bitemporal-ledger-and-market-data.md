# ADR-005: Bitemporal Ledger and Market Data

## Status
Accepted

## Context
Financial market prices, corporate actions, and dividend distributions are periodically revised, restated, or announced with backdated effective dates. To accurately analyze risk and explain risk changes over time ("Risk Diff"), the platform must distinguish between the transaction/market date and the time the platform learned of the data.

## Decision
Store ledger transactions, historical prices, and corporate actions with bitemporal timestamps:
1. **Effective Time (`effective_at` / `session_date`)**: The economic or business date when the transaction occurred or the market closed.
2. **Knowledge Time (`recorded_at` / `available_at`)**: The wall-clock system time when the record was ingested or amended.
