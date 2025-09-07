## Monitoring and Frontend Configuration

### 1) Monitoring Stack (Prometheus + Grafana)

- Services added under the tools profile in `docker-compose.yml`:
  - Prometheus at `http://localhost:9090`
  - Grafana at `http://localhost:3000` (default login: admin/admin)

Start monitoring:

```bash
docker compose --profile tools up -d prometheus grafana
```

Prometheus scrape config (`docker/prometheus/prometheus.yml`):

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "proxy_manager_api"
    metrics_path: /metrics
    static_configs:
      - targets: ["proxy_crawler:8000"]
```

Notes:

- The main API exposes metrics at `/metrics` (Prometheus format).
- If you add metrics to other services (e.g., html-to-markdown), add another `scrape_configs` entry with the container name and port.
- In Grafana, add a Prometheus data source using URL `http://prometheus:9090`.

Key metrics exposed:

- `proxy_pool_total` — total proxies in pool
- `proxy_pool_active` — active proxies in pool
- `proxy_api_requests_total{endpoint,method,status}` — request counters by route

### 2) Frontend Environment (.env)

Create `frontend/.env.local` with:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_ETL_BASE_URL=http://localhost:8001
VITE_REQUEST_TIMEOUT=15000

# Optional: set if backend API key middleware is enabled
VITE_API_KEY=
```

Behavior:

- `VITE_API_KEY` will be sent as `X-API-Key` header automatically by the frontend HTTP client.
- Default timeouts and base URLs can be adjusted per environment.

### 3) Quick Verification

Backend health:

```bash
curl http://localhost:8000/api/health
```

Metrics:

```bash
curl http://localhost:8000/metrics | head -50
```

Prometheus UI: `http://localhost:9090`

Grafana UI: `http://localhost:3001` → Add Prometheus data source → Build dashboard.

### 4) Default Grafana Dashboard

- Dashboard JSON: `docker/grafana/dashboards/proxy_system_overview.json`
- Import script (Windows):

```powershell
./tools/import_grafana_dashboard.ps1 -GrafanaUrl http://localhost:3001 -User admin -Pass admin -DashboardPath docker/grafana/dashboards/proxy_system_overview.json
```

- Import script (Linux/macOS):

```bash
export GRAFANA_URL=http://localhost:3001 GRAFANA_USER=admin GRAFANA_PASS=admin
sh ./tools/import_grafana_dashboard.sh
```
