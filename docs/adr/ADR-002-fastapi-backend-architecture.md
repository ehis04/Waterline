# ADR-002: FastAPI Architecture for Services

## Status
Accepted

## Context
The platform requires a modular backend supporting asynchronous API endpoints, robust OpenAPI schema generation, and high-performance analytical request handling decoupled from storage and presentation logic.

## Decision
1. Implement backend services using **FastAPI** with **Pydantic v2** for contract schemas and validation, and **SQLAlchemy 2** (asynchronous) for persistence.
2. Maintain strict separation of concerns:
   - Analytical calculations run exclusively in pure libraries (`risk_core`, `lookthrough`) with no database or network dependencies.
   - API endpoints coordinate parameter validation, authentication, and dispatch to computation workflows.
