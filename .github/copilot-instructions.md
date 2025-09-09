# Copilot project instructions

Goal: Help AI coding agents be instantly productive in this repo by knowing the architecture, conventions, and exact workflows used here.

## Big picture
- Monorepo-style FastAPI backend with three domains under `src/`:
  - `src/main.py` is the top FastAPI app. It merges Proxy Manager routes, mounts ETL (`/etl`) and HTML→Markdown (`/html2md`) apps, and exposes `/metrics` via Prometheus client.
  - `src/proxy_manager/` is the core service: proxy fetching, validation, pool management, and REST API. The modular routes live in `routes_*.py` and are aggregated by `api.py`.
  - `src/etl/` provides ETL orchestration and an API (`etl_api.py`) mounted at `/etl` by `main.py`.
  - `src/html_to_markdown/` offers conversion engines and its own API (`api_server.py`) mounted at `/html2md`.
- Observability: basic counters/gauges in `src/main.py` and `src/proxy_manager/api.py`, exposed at `/metrics`. Docker resources in `docker/` include Prometheus/Grafana configs.

## Service boundaries & data flow
- Proxy pipeline: crawlers (`src/proxy_manager/crawlers/*`) → validation (`validators/*`) → pools (`pools.py`) → API (`routes_*.py`).
- ETL pipeline: `etl_api.py` orchestrates `proxy_etl_pipeline.py`, `data_validator.py`, `monitoring_dashboard.py`, persisting via DB config in `database_config.py`.
- HTML→MD: adapters/converters in `src/html_to_markdown/*`, exposed via `api_server.py`.

## App composition
- `src/main.py` uses a FastAPI lifespan to start/stop a global ProxyManager instance and injects it into `src.proxy_manager.api` (via `api_shared.proxy_manager`).
- `src/proxy_manager/api.py` creates its own FastAPI app, includes routers:
  - `routes_proxies.py`, `routes_stats.py`, `routes_maintenance.py`, `routes_health_etl.py`, `routes_database.py`.
  - System endpoints include `/` (info), `/health` (redirect), `/api/system/health` (roll-up), `/metrics`.
- Pattern to add a new feature endpoint: create `src/proxy_manager/routes_<feature>.py` with an `APIRouter`, then include it in `api.py` via `app.include_router(...)`. Avoid importing `ProxyManager` at module top; import inside handlers or leverage `api_shared.get_proxy_manager()` to prevent cycles.

## Config & environment
- Settings via `src/config/settings.py` (Pydantic Settings). Common env vars: `ENVIRONMENT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `REDIS_SERVICE`.
- Docker Compose (`docker-compose.yml`) provisions Postgres, Redis, app, and optional Prometheus/Grafana.

## Developer workflows
- Package/deps: Project uses uv with pyproject + lock.
  - Install/refresh deps: `uv sync`
  - Run server (dev): `uv run python run_server.py` or `uv run uvicorn src.main:app --reload`
  - Run ETL API only: `uv run uvicorn src.etl.etl_api:etl_app --port 8001`
  - Tests: `uv run pytest -q` (pytest configured in `[tool.pytest.ini_options]`).
- URLs:
  - Main API/docs: `http://127.0.0.1:8000/` and `/docs`
  - Health: `/health` → `/api/health`, roll-up: `/api/system/health`
  - Metrics: `/metrics`
  - ETL API: `/etl/*` (when mounted by main) or port 8001 if run separately
  - HTML→MD API: `/html2md/*`

## Conventions & patterns
- Circular import avoidance: use deferred imports and `typing.TYPE_CHECKING`. Shared globals live in `src/proxy_manager/api_shared.py`.
- Metrics: define counters/gauges once and import where needed. Example: `REQUEST_COUNTER`, `POOL_GAUGE` in `src/main.py`.
- Routing: keep business logic in managers/services; route modules should be thin, async, and depend on `get_proxy_manager` from `api_shared`.
- Tests: prefer placing tests under `tests/`. Pytest matches `test_*.py` or `*_test.py` (see `pyproject.toml`). Import app code with `from src...`.

## Integration points
- DB/cache: Postgres and Redis from Compose; DB config in `database_config.py`, app env in `src/config/settings.py`.
- External sources: proxy crawlers under `src/proxy_manager/crawlers/` and integrations like `zmap_integration.py`.
- Frontend: separate Vite app in `frontend/` (not tightly coupled).

## Quick examples
- Add a new proxies endpoint: create `src/proxy_manager/routes_myfeat.py` with `router = APIRouter(prefix="/api/myfeat")`, implement handlers using `manager = Depends(get_proxy_manager)`, then include in `api.py`.
- Expose a new metric: import `from prometheus_client import Gauge`, define once (module-level), update inside handlers, surfaced via `/metrics`.

If any section seems out of date (e.g., routes or settings moved), open an issue/PR to update this file.
