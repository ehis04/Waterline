# ADR-004: Content-Addressed Computation DAG and Verification Receipts

## Status
Accepted

## Context
Calculations must provide complete transparency and auditability. Users and automated verifiers need verifiable provenance showing exactly how any risk figure or attribution metric was computed.

## Decision
1. Execute multi-step computations via a directed acyclic graph (DAG) composed of deterministic, pure nodes.
2. Node inputs, parameters, and function identifiers are serialized via Canonical JSON (RFC 8785) and hashed using SHA-256 to create immutable content-addressed references.
3. Every computation run generates an inspectable calculation receipt detailing input hashes, intermediate steps, execution timestamps, and engine versions.
