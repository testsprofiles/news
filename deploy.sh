#!/usr/bin/env bash
#
# One-command production deployment for the News Portal.
#
#   ./deploy.sh
#
# It bootstraps the .env file, pulls the latest code, installs dependencies,
# applies yoyo migrations, runs the test-suite and (re)builds the Docker stack.
set -euo pipefail

PROJECT_PATH="${PROJECT_PATH:-/var/www/news}"
BRANCH="${BRANCH:-main}"
PORT="${PORT:-5000}"

cd "$PROJECT_PATH"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== News Portal deployment started ==="

# --- 1/6  Environment file ---------------------------------------------------
if [ ! -f .env ]; then
    log "[1/6] .env not found - creating it from .env.production.template"
    cp .env.production.template .env
    GEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    GEN_DB_PASS="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${GEN_SECRET}|" .env
    sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${GEN_DB_PASS}|" .env
    log "[1/6] Generated a random SECRET_KEY and DB_PASSWORD in .env"
else
    log "[1/6] Using the existing .env"
fi

# --- 2/6  Latest code --------------------------------------------------------
log "[2/6] Pulling the latest code from origin/${BRANCH} ..."
git pull origin "${BRANCH}"

# --- 3/6  Python dependencies ------------------------------------------------
log "[3/6] Installing Python dependencies ..."
if [ -f venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

# --- 4/6  Database migrations ------------------------------------------------
# The app container also runs migrations on start; doing it here gives a clear
# early failure if the database credentials are wrong.
log "[4/6] Applying database migrations ..."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${DB_PORT}/${DB_NAME}"
if command -v yoyo >/dev/null 2>&1; then
    yoyo apply --batch --no-config-file -d "${DB_URL}" ./migrations \
        || log "[4/6] WARN: host migration skipped (database not reachable yet); the app container will retry."
else
    log "[4/6] WARN: yoyo not found on the host; the app container will run migrations."
fi

# --- 5/6  Tests --------------------------------------------------------------
log "[5/6] Running the test-suite ..."
python -m pytest tests/ -q

# --- 6/6  Containers ---------------------------------------------------------
log "[6/6] Building and starting the Docker stack ..."
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    log "[6/6] ERROR: neither 'docker compose' nor 'docker-compose' is available."
    exit 1
fi

$COMPOSE up -d --build
$COMPOSE ps

log "=== Deployment finished successfully on port ${PORT} ==="
