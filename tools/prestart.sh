#!/usr/bin/env sh
set -e

# Export DB connection from env (already provided via ENV/compose)

echo "[prestart] Running Alembic migrations..."
alembic upgrade head

echo "[prestart] Starting API..."
exec "$@"
