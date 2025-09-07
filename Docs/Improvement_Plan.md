## JasonSpider Improvement Plan (Engineering Execution Guide)

### 1) Objectives

- Deliver a production-ready Proxy Crawler & Manager with consistent entrypoint, working DB schema, and reliable health checks.
- Unify configuration and dependencies to reduce operational drift and simplify deployments.
- Strengthen security and observability for safer operations and easier troubleshooting.

### 2) Scope

- In scope: backend APIs (main/proxy-manager/html-to-markdown), Docker/Compose, DB schema/migrations, config/unification, basic security (CORS/API key), tests, monitoring endpoints, Windows 10 + Docker Compose dev flow.
- Out of scope: large feature additions, UI redesign, heavy performance refactors beyond quick wins.

### 3) Current State Summary (as observed)

- Multiple FastAPI apps: `src/main.py` (basic), `src/proxy_manager/api.py` (full API), `src/html_to_markdown/api_server.py` (ETL service).
- Dockerfile runs `src.main:app`, not the real proxy-manager API; healthcheck points to `/health` but proxy-manager exposes `/api/health`.
- DB access uses `asyncpg` in `proxy_manager/database_service.py` but no Alembic migrations/schema present.
- Config split between `src/config/config_loader.py` and top-level `database_config.py`.
- Dependencies defined in both `pyproject.toml` and `requirements.txt`.
- Tests reside outside `tests/` while pytest config only looks at `tests/`.
- CORS is wide-open; API key/rate-limit only modeled, not enforced.
- Monitoring API present but not mounted; health checks don’t probe DB/Redis.

### 4) Risks & Assumptions

- Assumes Windows 10 dev with Docker Compose; file permission quirks for bind mounts may occur.
- Assumes Postgres/Redis containers are the canonical dev backing services.
- Changing entrypoint may break ad-hoc scripts relying on `src.main:app`. We will preserve a dev script.

### 5) Workstreams and Deliverables

P0 — Platform correctness and reliability

1. Align container entrypoint to proxy manager API

   - Rationale: Ensure the primary API is reachable (and matches frontend expectations).
   - Deliverables: Dockerfile CMD uses `src.proxy_manager.api:app`; HEALTHCHECK path `/api/health`.
   - Acceptance: `docker compose up -d` → 200 OK on `GET /api/health`.

2. Add Alembic migrations and initialize DB schema

   - Rationale: Make DB reproducible and versioned.
   - Deliverables: Alembic set up; initial migration for `proxy_nodes` + indexes.
   - Acceptance: `alembic upgrade head` runs cleanly in container and locally.

3. Real health checks (DB/Redis)
   - Rationale: Surface true service health; fail fast.
   - Deliverables: `/api/health` verifies Postgres/Redis connectivity and returns status.
   - Acceptance: Simulate DB/Redis down → endpoint reports degraded/unhealthy.

P1 — Operational hygiene and security 4. Unify configuration

- Rationale: Single source of truth; predictable overrides.
- Deliverables: Consolidated settings (BaseSettings) that bridge `config_loader` and `database_config`.
- Acceptance: Environment variables override correctly in both Docker and local.

5. Tighten security

   - Rationale: Reduce exposure surface.
   - Deliverables: Restrictive CORS (env-driven), API key middleware for admin endpoints, basic rate limiting.
   - Acceptance: Requests without API key rejected; allowed origins only.

6. Standardize dependencies

   - Rationale: Avoid duplication and drift.
   - Deliverables: Choose one (A) `pyproject.toml` + `uv` (or Poetry) OR (B) `requirements.txt`; Dockerfile uses the chosen path consistently.
   - Acceptance: Fresh build uses single dependency source; CI lock present.

7. Test discovery and coverage
   - Rationale: Ensure existing tests run.
   - Deliverables: Pytest config updated to include root `test_*.py`; add minimal API/DB integration tests.
   - Acceptance: `pytest` passes; coverage report includes API modules.

P2 — Observability and DX 8. Enable monitoring API and Prometheus metrics

- Deliverables: Mount monitoring app; expose `/metrics`; basic process and pool stats.
- Acceptance: Prometheus can scrape; dashboard shows pool health.

9. Docker volumes/permissions on Windows
   - Deliverables: Startup script to ensure write permissions for `./logs`, `./data`; docs for Windows bind-mounts.
   - Acceptance: No write-permission errors in containers; logs flow to host.

### 6) Implementation Steps (High-level)

Step A (P0):

- Update Dockerfile: CMD → `src.proxy_manager.api:app`, HEALTHCHECK → `/api/health`.
- Add health probe logic in `proxy_manager/api.py` (DB/Redis ping).
- Add Alembic; initial migration for `proxy_nodes` and helpful indexes; auto-run on container start.

Step B (P1):

- Consolidate configuration via Pydantic BaseSettings; keep backward compatibility with current loaders.
- Implement CORS restriction, API key middleware, simple rate limiting (in-memory or Redis-backed).
- Choose dependency strategy; update Dockerfile and docs; remove duplicates.
- Fix pytest discovery; add minimal integration tests.

Step C (P2):

- Mount monitoring API; export Prometheus metrics.
- Improve Windows bind-mount permissions, add notes to README.

### 7) Timeline (indicative)

- Week 1: Step A complete; end-to-end up via Docker Compose.
- Week 2: Step B config/security/deps/test consolidation.
- Week 3: Step C observability and Windows DX polish.

### 8) Acceptance Criteria Checklist

- Entrypoint: 200 OK on `/api/health`; `/api/*` endpoints operational.
- DB: Alembic migration applies cleanly; queries return data; indexes exist.
- Health: Reports DB/Redis status accurately; Docker healthcheck turns unhealthy if DB is down.
- Config: Single-source settings; env overrides verified.
- Security: CORS restricted; API Key enforced for admin routes; rate limiting active.
- Tests: `pytest` runs and passes; basic coverage on API modules.
- Monitoring: `/metrics` exposes counters/gauges for pools and service health.
- Windows: No permission errors writing to `logs`/`data` with bind mounts.

### 9) Rollback Strategy

- Keep prior Docker tag for quick rollback.
- Alembic down migration for schema changes when feasible; otherwise use additive migrations only.

### 10) Ownership

- Backend platform: Core maintainers.
- DB schema/migrations: Backend + DBA (if available).
- Security and config: Backend platform.
- Monitoring: Backend platform / DevOps.

### 11) References

- Entrypoints: `src/main.py`, `src/proxy_manager/api.py`, `src/html_to_markdown/api_server.py`
- DB access: `src/proxy_manager/database_service.py`, `database_config.py`
- Compose: `docker-compose.yml`; Docker image: `Dockerfile`
