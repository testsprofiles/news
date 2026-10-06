#!/usr/bin/env bash
#
# One-command production deployment for the News Portal.
#
#   ./deploy.sh
#
# The script adapts to the host it runs on:
#   * docker-compose  -> builds the app image and starts the app+db stack
#   * systemd         -> restarts the app.service gunicorn unit (native PostgreSQL)
#
# Steps:
#   1) reconcile .env    2) conflict-safe git pull   3) Python dependencies
#   4) yoyo migrations   5) pytest                    6) start the runtime
#   7) health check
set -euo pipefail

PROJECT_PATH="${PROJECT_PATH:-/var/www/news}"
BRANCH="${BRANCH:-main}"
PORT="${PORT:-5000}"

cd "$PROJECT_PATH"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Returns 0 when the URL answers with HTTP 200.
http_ok() {
    python3 - "$1" <<'PY' >/dev/null 2>&1
import sys
import urllib.request
sys.exit(0 if urllib.request.urlopen(sys.argv[1], timeout=3).status == 200 else 1)
PY
}

# --- 0/7  Detect the runtime -------------------------------------------------
# docker-compose.yml may write secrets that must stay out of git, so prefer the
# container stack only when the compose CLI is actually present.
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
    RUNTIME="compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
    RUNTIME="compose"
elif systemctl cat app.service >/dev/null 2>&1; then
    COMPOSE=""
    RUNTIME="systemd"
else
    COMPOSE=""
    RUNTIME="none"
fi

log "=== News Portal deployment started (branch=${BRANCH}, path=${PROJECT_PATH}, runtime=${RUNTIME}) ==="

if [ "${RUNTIME}" = "none" ]; then
    log "[0/7] ERROR: found neither docker compose nor an app.service unit."
    log "[0/7]        Install Docker (with the compose plugin) or the app.service unit."
    exit 1
fi

# --- 1/7  Environment file ---------------------------------------------------
# Local and server settings stay identical. Secrets are NEVER hardcoded here and
# are NEVER printed: they are read from .env, generated once when still blank.
log "[1/7] Reconciling .env ..."
if [ ! -f .env ]; then
    log "[1/7] .env not found - seeding it from .env.production.template"
    cp .env.production.template .env
fi

RUNTIME="${RUNTIME}" python3 - <<'PY'
import os
import secrets
from pathlib import Path

runtime = os.environ["RUNTIME"]

# Non-secret settings that must be identical on every machine.
STRUCTURAL = [
    ("FLASK_ENV", "production"),
    ("FLASK_DEBUG", "False"),
    ("FLASK_PORT", "5000"),
    ("PORT", "5000"),
    ("GUNICORN_WORKERS", "4"),
    ("DB_PORT", "5432"),
    ("DB_NAME", "news_db"),
    ("DB_USER", "postgres"),
    ("SERVER_IP", "2.29.24.32"),
    ("SSH_USER", "root"),
    ("PROJECT_PATH", "/var/www/news"),
]
# DB_HOST depends on where PostgreSQL lives:
#   compose -> the "db" service on the compose network
#   systemd -> native PostgreSQL on the host loopback
if runtime == "compose":
    STRUCTURAL.append(("DB_HOST", "db"))
elif runtime == "systemd":
    STRUCTURAL.append(("DB_HOST", "127.0.0.1"))

# Secrets: keep whatever is already configured, fill in safe gaps only.
PLACEHOLDERS = ("", "change_me", "change_me_strong_db_password",
                "change_me_to_a_random_32_byte_or_longer_secret")
GENERATED = {
    "SECRET_KEY": lambda: secrets.token_hex(32),   # >=32 bytes for HS256
    "DB_PASSWORD": lambda: secrets.token_hex(16),
}
# Optional keys that stay empty (bot disabled) until the owner fills them in.
OPTIONAL = ["BOT_TOKEN", "CHANNEL_ID", "WEBAPP_URL"]

wanted = dict(STRUCTURAL)
for key, make in GENERATED.items():
    wanted.setdefault(key, None)

path = Path(".env")
lines = path.read_text().splitlines() if path.exists() else []

seen, out, added, updated = set(), [], [], []
for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith("#") and "=" in stripped:
        key, value = stripped.split("=", 1)
        key, value = key.strip(), value.strip()
        seen.add(key)
        if key in wanted and wanted[key] is not None:
            new = f"{key}={wanted[key]}"
            if new != f"{key}={value}":
                updated.append(key)
            line = new
        elif key in GENERATED and value in PLACEHOLDERS:
            line = f"{key}={GENERATED[key]()}"
            updated.append(key)
    out.append(line)

for key, value in STRUCTURAL:
    if key not in seen:
        out.append(f"{key}={value}")
        added.append(key)
for key in list(GENERATED) + OPTIONAL:
    if key not in seen:
        default = GENERATED[key]() if key in GENERATED else ""
        out.append(f"{key}={default}")
        added.append(key)

if added:
    out.append("")
path.write_text("\n".join(out).rstrip("\n") + "\n")

print(f"[1/7] .env ok ({runtime} runtime): {len(seen) + len(added)} keys, "
      f"{len(added)} added, {len(updated)} updated")
if added:
    print("[1/7]   added   : " + ", ".join(added))
if updated:
    print("[1/7]   updated : " + ", ".join(updated))
print("[1/7]   note    : values are never printed; .env stays git-ignored.")
PY

# --- 2/7  Latest code (conflict-safe) ----------------------------------------
log "[2/7] Fetching origin/${BRANCH} ..."
git fetch origin "${BRANCH}"

# A half-finished rebase/merge on the server would make `git pull` abort and
# leave the deploy stuck, so clear it first.
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
    log "[2/7] Clearing an in-progress rebase ..."
    git rebase --abort || true
fi
if [ -f .git/MERGE_HEAD ]; then
    log "[2/7] Clearing an in-progress merge ..."
    git merge --abort || true
fi

# Stash uncommitted *tracked* edits (untracked/ignored files such as .env and
# CHANGELOG_JOURNAL.txt are never touched).
STASHED=0
if ! git diff --quiet || ! git diff --cached --quiet; then
    log "[2/7] Local changes detected - stashing before the pull ..."
    git stash push --message "deploy-autostash-$(date +%Y%m%d-%H%M%S)"
    STASHED=1
fi

if git pull --ff-only origin "${BRANCH}"; then
    log "[2/7] Fast-forwarded to $(git rev-parse --short HEAD)"
elif git pull --no-rebase origin "${BRANCH}"; then
    log "[2/7] Merged origin/${BRANCH} into $(git rev-parse --short HEAD)"
else
    log "[2/7] ERROR: git pull failed - resolve the conflict manually, then re-run ./deploy.sh"
    exit 1
fi

if [ "${STASHED}" -eq 1 ]; then
    if git stash pop; then
        log "[2/7] Re-applied the stashed local changes"
    else
        log "[2/7] WARN: stashed changes could not be re-applied cleanly;"
        log "[2/7]       they are safe in 'git stash list' - resolve when convenient."
    fi
fi

# --- 3/7  Python dependencies ------------------------------------------------
log "[3/7] Installing Python dependencies ..."
if [ -f venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

# --- 4/7  Database migrations ------------------------------------------------
# Read the credentials from .env and target the host loopback: the compose stack
# publishes PostgreSQL on 127.0.0.1, and systemd uses native PostgreSQL there.
log "[4/7] Applying database migrations ..."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${DB_PORT}/${DB_NAME}"
if command -v yoyo >/dev/null 2>&1; then
    yoyo apply --batch --no-config-file -d "${DB_URL}" ./migrations \
        || log "[4/7] WARN: host migration skipped (database not reachable yet); the app container will retry."
else
    log "[4/7] WARN: yoyo not found on the host; the app will run migrations on start."
fi

# --- 5/7  Tests --------------------------------------------------------------
log "[5/7] Running the test-suite ..."
python -m pytest tests/ -q

# --- 6/7  Start the runtime --------------------------------------------------
if [ "${RUNTIME}" = "compose" ]; then
    log "[6/7] Building and starting the Docker stack ..."
    $COMPOSE up -d --build
    $COMPOSE ps
else
    log "[6/7] Restarting the app.service gunicorn unit ..."
    systemctl restart app.service
    systemctl is-active app.service
fi

# --- 7/7  Health check -------------------------------------------------------
log "[7/7] Waiting for the app on http://127.0.0.1:${PORT}/health ..."
HEALTHY=0
for _ in $(seq 1 30); do
    if http_ok "http://127.0.0.1:${PORT}/health"; then
        HEALTHY=1
        break
    fi
    sleep 2
done

if [ "${HEALTHY}" -eq 1 ]; then
    log "[7/7] App is healthy on port ${PORT}."
    log "=== Deployment finished successfully on port ${PORT} ==="
else
    log "[7/7] ERROR: the app did not answer on port ${PORT} within 60s."
    if [ "${RUNTIME}" = "compose" ]; then
        log "[7/7] Inspect logs with: ${COMPOSE} logs --tail=100 app"
    else
        log "[7/7] Inspect logs with: journalctl -u app.service -n 100 --no-pager"
    fi
    exit 1
fi
