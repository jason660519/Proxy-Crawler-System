## Phase 3 Observations and Status Report (Proxy Crawler System)

### Executive Summary
- The backend is now instrumented with Prometheus metrics for the main API and the html-to-markdown service; Grafana and default dashboards are available and embedded in the frontend.
- Multiple proxy acquisition paths exist: legacy HTML crawlers, unified fetchers (JSON/local and generic web scrape), and advanced fetchers (ProxyScrape API, GitHub lists; Shodan/Censys optional with keys). Validation and pool management are handled in `ProxyManager`.
- The ETL pipeline aligns with a clear directory structure (raw/processed/validated/reports), database loading via Alembic-managed schema, and is mountable under the API (`/etl`). Some ETL API surface is scaffolded and can be iterated.
- Immediate gaps: add aggregated `/metrics/summary` and `/metrics/trends` endpoints on the main API, complete ETL adapters that ingest directly from `ProxyManager`, and finalize alerting rules for scrape failures.

---

### Data Acquisition Methods (What Exists vs. Works)

- HTML crawler adapters (under `src/proxy_manager/crawlers/`):
  - SSLProxies (`sslproxies_org__proxy_crawler__.py`): table scraping with fallbacks; dedup; rate limiting.
    - Status: Works in general but subject to upstream HTML changes and rate limits. Expect intermittent flakiness.
  - Free-Proxy-List (`free_proxy_list_net__proxy_crawler__.py`): targets `#proxylisttable` with fallbacks; dedup; supports socks/http pages.
    - Status: Typically works; also subject to occasional HTML layout shifts and anti-scraping.
  - Geonode (`geonode_com__proxy_crawler__.py`): multiple parsing strategies (table, JSON-in-HTML, card); attempts optional API patterns.
    - Status: Best-effort scraping; may be flaky if content is dynamic or guarded.
  - Notes: These crawlers are orchestrated by `CrawlerManager` (validation, dedup, ETL-mode outputs), but they are not the default acquisition path used by `ProxyManager` runtime.

- Unified fetchers (under `src/proxy_manager/fetchers.py`):
  - `JsonFileFetcher`: reads `proxy_list.json` when present.
    - Status: Works (file exists in repo). Deterministic, good for baseline/testing.
  - `WebScrapeFetcher`: generic HTTP fetch + custom parser hook.
    - Status: Available; requires a parser function to be wired for specific sites.
  - `ProxyFetcherManager`: aggregates the above and also defers to advanced fetchers; deduplicates results.

- Advanced fetchers (under `src/proxy_manager/advanced_fetchers.py`), enabled by `AdvancedProxyFetcherManager` in `ProxyManager`:
  - ProxyScrape API: unauthenticated usage typically works (may be rate-limited).
    - Status: Works without API key but limited; add key for reliability.
  - GitHub lists: pulls public curated lists (e.g., `TheSpeedX/PROXY-List`).
    - Status: Works; subject to repo availability and content quality.
  - Shodan, Censys: discovery-based; require credentials.
    - Status: Disabled unless keys are provided; once configured, workable but higher variance and slower.

- Manager integration:
  - `ProxyManager` uses `ProxyFetcherManager` + `AdvancedProxyFetcherManager`, optional pre-scan, batch validation, then pool insertion.
  - `CrawlerManager` is a separate path for HTML crawlers and ETL-mode outputs; use it when you want strict ETL foldering and standalone reports.

Summary classification (expected):
- Working now: `JsonFileFetcher`, ProxyScrape (limited), GitHub lists, `ProxyManager` validation/pools, Prometheus `/metrics` (main + html2md), Grafana dashboards, frontend Grafana embedding.
- Working but potentially flaky: `sslproxies`, `free-proxy-list`, `geonode` crawlers (upstream layout/anti-bot dependent).
- Not working until configured: Shodan, Censys fetchers (need API credentials); ETL API advanced flows (scaffolded, needs wiring to real data).

---

### ETL Compliance and Current Flow

- Directory layout: `data/raw`, `data/processed`, `data/validated`, `data/reports` are used by the ETL pipeline and by `CrawlerManager` ETL mode.
- Database: Alembic migrations exist and run on container start (`tools/prestart.sh`); `proxy_nodes` schema created with indices and unique `(host, port, protocol)`.
- Validation: `ProxyManager` performs batch validation and updates metrics/scores before pool insertion; ETL pipeline also validates when ingesting files.
- Loading: ETL loads into Postgres (asyncpg) and can cache hot entries in Redis.
- API mounting: ETL API (`/etl`) is mountable from `src/proxy_manager/api.py` and exposes job/monitoring stubs.

Compliance assessment:
- Extract: Multiple sources supported (file, crawlers, APIs) – OK.
- Transform: Normalization to `ProxyNode`, dedup, scoring hooks – OK.
- Validate: Batch validator in `ProxyManager` and ETL – OK.
- Load: Postgres+Redis implemented; Alembic-managed – OK.
- Gaps: Direct adapter to feed `ProxyManager` pools into ETL pipeline outputs (instead of file-sourced ETL) can be finalized; ETL API surfaces are partially scaffolded and can be bound to real runs.

---

### Monitoring Coverage (What the dashboards can show now)

- Main API (`proxy_manager`):
  - `proxy_api_requests_total` (by endpoint/method/status)
  - `proxy_api_request_duration_seconds` histogram
  - `proxy_pool_total`, `proxy_pool_active` gauges (updated on health/stats)
  - Exposed at `/metrics`; Prometheus scrape configured.

- html-to-markdown service:
  - `html2md_requests_total` and `html2md_request_duration_seconds` via middleware
  - Exposed at `/metrics`; scrape job added.

- Grafana:
  - Default dashboards imported: system overview and proxy validation overview.
  - Frontend embeds dashboards via configurable `VITE_GRAFANA_URL` (default `http://localhost:3001`).

- Gaps/next:
  - Add `/metrics/summary` and `/metrics/trends` endpoints on main API to support native frontend charts without Grafana embedding.
  - Add alert rules: scrape down for html2md, low active proxies, high latency/error-rate alerts.
  - Optionally add DB/Redis pool metrics and validator success-rate gauges.

---

### Findings from Recent Tests (based on code and typical behavior)

- It’s expected that some HTML crawlers succeed and some fail intermittently due to upstream changes and anti-scraping. Free-Proxy-List and SSLProxies are the most stable among HTML sources; Geonode can work but is more sensitive.
- Advanced fetchers (ProxyScrape/GitHub) provide stable baselines and should be used as primary feeds; discovery (Shodan/Censys) should be additive once keys are configured and rate limits are handled.
- `JsonFileFetcher` provides deterministic testing and can seed the pools.

Recommended quick checks you can run:
- Verify Prometheus scrapes: `http://localhost:9090/targets` → both jobs up.
- Verify metrics endpoints: `GET http://localhost:8000/metrics`, `GET http://localhost:8001/metrics`.
- Kick a manual fetch-and-validate via `ProxyManager.fetch_proxies()` path (API endpoint or script) and confirm pool gauges increase.

---

### Next Actions (Phase 3)

1) Backend API
- Add `/api/metrics/summary`: aggregate request counts, error rates, pool sizes.
- Add `/api/metrics/trends`: simple time-bucketed trends (in-memory or via PromQL proxy), backing native frontend charts.

2) ETL
- Implement adapter to export current pools from `ProxyManager` directly into ETL stages (raw→processed→validated→reports) for unified history and auditability.
- Wire ETL API run endpoints to real ETL executions and persist job summary artifacts.

3) Monitoring/Alerting
- Add alerting for `html_to_markdown` metrics scrape down and high request error rates.
- Optional: expose DB/Redis metrics; add validator success-rate gauges.

4) Frontend
- Consume `/api/metrics/summary` and `/api/metrics/trends` for native charts in an “Ops” page; keep Grafana embedding as advanced view.

---

### Risk/Notes
- HTML sources may throttle/ban; respect rate limits and add rotating headers/proxies if needed.
- Upstream schema drift can break crawlers; keep defensive parsing and fast fallbacks.
- Discovery feeds (Shodan/Censys) are high-variance and cost/time-sensitive; integrate with care and budgets.

---

### Appendix: Key Files and Endpoints
- Acquisition
  - Crawlers: `src/proxy_manager/crawlers/*`
  - Unified fetchers: `src/proxy_manager/fetchers.py`
  - Advanced fetchers: `src/proxy_manager/advanced_fetchers.py`
- Orchestration
  - Manager: `src/proxy_manager/manager.py`
  - Pools/validation: `src/proxy_manager/pools.py`, `src/proxy_manager/validators/*`
- ETL
  - Pipeline: `src/etl/proxy_etl_pipeline.py`
  - API: `src/etl/etl_api.py` (mounted at `/etl`)
- Monitoring
  - Metrics: `GET /metrics` (main API and html2md)
  - Prometheus: `docker/prometheus/prometheus.yml`
  - Grafana dashboards: `docker/grafana/dashboards/*.json`
  - Frontend embedding: `frontend/src/components/dashboard/OperationsDashboard.tsx`


