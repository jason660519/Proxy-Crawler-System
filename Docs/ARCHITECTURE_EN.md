# Architecture Overview (English)

This document supplements existing Chinese docs and reflects the new Service Layer introduced (FetchService, ValidationService, PersistenceService).

## Layers

1. API (FastAPI apps: main, proxy, html2md, etl)
2. Orchestration (ProxyManager facade)
3. Service Layer (extracted cohesive units)
4. Core Modules (pools, validators, scanners, fetchers)
5. Infrastructure (future: Redis / Postgres; current JSON snapshots)

## Concurrency

Fetch operations serialized via `asyncio.Lock` to avoid upstream overload.

## Metrics

Prometheus endpoint `/metrics` exposes request counter + pool active gauges.

## Roadmap

- Phase 2: Redis-backed pool store
- Phase 3: Postgres historical analytics
- Phase 4: Streaming/gzip export

## Extension Points

Implement new fetcher -> register in `fetcher_manager`.
Add validation heuristic -> extend `BatchValidator` and surface through `ValidationService`.

## Testing Guidance

- Unit test service classes (mock manager parts)
- Integration test metrics & pool stats.
