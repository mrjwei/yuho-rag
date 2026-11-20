## 2026-11-19 — Use one Postgres for metadata and vectors

**Context:** need filtering by company/year/section plus vector search.
**Decision:** Postgres 17 + pgvector; exact search (no ANN index) for v1.
**Why:** ~8k chunks → exact scan is milliseconds; one SQL query does filter+rank; no extra service.
**Revisit if:** corpus > ~200k chunks or p95 retrieval > 200 ms.
