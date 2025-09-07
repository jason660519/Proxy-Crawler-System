## ETL Pipeline Overview (Proxy Crawler System)

### 1) Summary

This document describes the Extract-Transform-Load pipeline for the Proxy Crawler system as of the current architecture. It covers services, data flow, storage locations, health, and operations.

### 2) Services and Components

- Main API: `src/proxy_manager/api.py` (port 8000)
  - Provides proxy pool APIs, health checks, admin operations, optional ETL sub-app mount under `/etl` when available.
  - Health check probes Postgres and Redis.
- HTML→Markdown Service: `src/html_to_markdown/api_server.py` (port 8001)
  - Dedicated FastAPI service for content conversion and batch processing.
  - Data directories are mounted via Docker Compose.
- Database: PostgreSQL (container `postgres_db`) with Alembic migrations.
- Cache: Redis (container `redis_cache`).

### 3) Data Flow (Mermaid)

```mermaid
graph TB
  subgraph "Extract"
    E1[HTTP requests] --> E2[Fetch HTML]
    E2 --> E3{Content type?}
    E3 -->|Static| E4[Parse with BeautifulSoup]
    E3 -->|Dynamic| E5[Playwright/Selenium]
    E4 --> E6[Extract tables]
    E5 --> E6
  end

  subgraph "Transform"
    T1[Raw proxy data] --> T1A[HTML→Markdown (Service @ 8001)]
    T1A --> T1B[LLM-assisted parsing/structuring]
    T1B --> T2[IP validation]
    T2 --> T3[Port normalization]
    T3 --> T4[Protocol standardization]
    T4 --> T5[Country code mapping]
    T5 --> T6[Anonymity classification]
    T6 --> T7[Speed unit unification]
    T7 --> T8[Quality scoring]
  end

  subgraph "Validate"
    V1[Async validation queue] --> V2[Connectivity test]
    V2 --> V3[Speed test]
    V3 --> V4[Anonymity test]
    V4 --> V5[Geo verification]
    V5 --> V6[Composite score]
  end

  subgraph "Load"
    L1[Valid data] --> L2[Write to Postgres]
    L1 --> L3[Update Redis cache]
    L2 --> L4[Generate Markdown report]
    L3 --> L5[API-ready pools]
  end

  E6 --> T1
  T8 --> V1
  V6 --> L1
```

### 4) Storage Layout

- Raw: `data/raw/{source}_{timestamp}.json`
- Processed: `data/processed/{source}_{timestamp}.json`
- Converted Markdown: `data/processed/{source}_{timestamp}.md`
- Validated: `data/validated/{source}_{timestamp}.json`
- Reports: `data/reports/{source}_{timestamp}_proxies.md`
- HTML→Markdown service (via Docker Compose):
  - Input: `data/raw/html-to-markdown` → `/app/input`
  - Processing: `data/processed/html-to-markdown` → `/app/processing`
  - Output: `data/transformed/html-to-markdown` → `/app/output`

### 5) Operations

- Migrations: Alembic runs automatically on container start (prestart script) to ensure schema (e.g., `proxy_nodes`) is up-to-date.
- Health: Main API `/api/health` returns overall `healthy/degraded/unhealthy` based on API runtime, Postgres, and Redis.
- Metrics: (optional) Prometheus metrics can be exposed at `/metrics` (see Monitoring section when enabled).
- Admin endpoints (protected by API key when enabled):
  - `/api/validate`, `/api/cleanup`, `/api/export`, `/api/etl/sync`, `/api/batch/validate`

### 6) HTML→Markdown Service API (8001)

- `GET /health`: service liveness
- `POST /convert`: single conversion (returns Markdown and metadata)
- `POST /convert/batch`: batch conversion
- `POST /upload`: upload HTML file for conversion

### 7) Environment and Config

- Unified settings via Pydantic BaseSettings: `src/config/settings.py`
- Key environment variables:
  - Database: `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST` (or `DB_SERVICE` in Docker), `DB_PORT`
  - Redis: `REDIS_PASSWORD` (optional), `REDIS_HOST` (or `REDIS_SERVICE` in Docker), `REDIS_PORT`, `REDIS_DB`
  - Security: `API_KEY_ENABLED`, `API_KEYS` (comma-separated), CORS origins via settings

### 8) Change Log (compatibility)

- No breaking changes to the HTML→Markdown service endpoints or volumes.
- Main API now performs real DB/Redis health checks and runs Alembic migrations at startup; this does not change ETL data contracts.
- Configuration is unified; existing env vars continue to work.
