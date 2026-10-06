#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-news_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
PORT="${PORT:-5000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD PORT GUNICORN_WORKERS

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."
python - <<'PY'
import os
import sys
import time

import psycopg2

attempts = 30
for attempt in range(1, attempts + 1):
    try:
        psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "news_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        ).close()
        print(f"[entrypoint] Database is ready (attempt {attempt}).")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - we want to retry on any failure
        print(f"[entrypoint] Database not ready yet ({exc}); retrying in 2s ...")
        time.sleep(2)

print("[entrypoint] Database did not become ready in time.", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Applying database migrations ..."
yoyo apply --batch --no-config-file \
    -d "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
    ./migrations

echo "[entrypoint] Starting gunicorn on 0.0.0.0:${PORT} ..."
exec gunicorn \
    --workers "${GUNICORN_WORKERS}" \
    --bind "0.0.0.0:${PORT}" \
    --access-logfile - \
    --error-logfile - \
    app:app
