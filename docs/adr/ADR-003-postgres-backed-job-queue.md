# ADR-003: Postgres-Backed Job Queue

## Status
Accepted

## Context
Asynchronous jobs (portfolio recalculations, snapshot valuations, and batch look-through expansions) require resilient background execution with retries and status tracking. Introducing separate queue infrastructure (such as Redis and Celery) increases early operational overhead and deployment complexity.

## Decision
1. Utilize a PostgreSQL-backed task queue pattern (such as Procrastinate) leveraging transactional guarantees alongside application state.
2. Wrap all job scheduling and worker definitions behind an abstraction layer so the underlying backend can transition to distributed queues if throughput warrants.
