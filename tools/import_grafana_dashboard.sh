#!/usr/bin/env sh
set -e

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3001}
USER=${GRAFANA_USER:-admin}
PASS=${GRAFANA_PASS:-admin}
DASHBOARD_JSON=./docker/grafana/dashboards/proxy_system_overview.json

echo "Importing dashboard to $GRAFANA_URL"
curl -s -u "$USER:$PASS" -H "Content-Type: application/json" \
  -X POST "$GRAFANA_URL/api/dashboards/db" \
  -d "$(jq -n --argjson dashboard "$(cat $DASHBOARD_JSON)" '{dashboard: $dashboard, overwrite: true}'))"
echo "Done."


