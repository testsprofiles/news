#!/usr/bin/env bash
set -euo pipefail

echo "=== News Portal Deployment ==="
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

PROJECT_PATH="${PROJECT_PATH:-/var/www/news}"

cd "$PROJECT_PATH"

echo "[1/5] Pull latest code..."
git pull origin main

echo "[2/5] Install dependencies..."
python -m pip install -r requirements.txt --quiet

echo "[3/5] Run database migrations..."
if command -v yoyo >/dev/null 2>&1; then
  echo "Running yoyo migrations..."
  yoyo apply ./migrations || echo "WARN: yoyo migrations failed - check DB connectivity"
else
  echo "WARN: yoyo command not found, skipping migrations"
fi

echo "[4/5] Run tests..."
python -m pytest tests/ -q || echo "WARN: Some tests failed - check output above"

echo "[5/5] Start/rebuild services with Docker Compose..."
if command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml ]; then
  docker compose up -d --build
  echo "Docker Compose started."
else
  echo "WARN: Docker or docker-compose.yml not available, skipping compose up."
fi

echo "=== Deployment finished at $(date '+%Y-%m-%d %H:%M:%S') ==="
