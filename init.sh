#!/usr/bin/env bash
# =============================================================================
# init.sh — Gets the ClearMD development environment READY (idempotent).
# =============================================================================
#   • INSIDE THE DEVCONTAINER: installs dependencies with uv. Triggered by the
#     devcontainer postCreateCommand.
#   • HOST (Docker CLI present): builds and starts the container, then the same inside.
# ClearMD has no database (ADR-0002): no governance, no migrations.
# ENVIRONMENT: development only. APP_ENV 'prod'/'production' aborts.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose"

# --- Environment guard: development only -------------------------------------
APP_ENV="${APP_ENV:-$(grep -E '^APP_ENV=' .env 2>/dev/null | cut -d= -f2- || true)}"
APP_ENV="${APP_ENV:-dev}"
case "${APP_ENV,,}" in
  prod*)
    echo "✋ APP_ENV=$APP_ENV — init.sh is for development only." >&2
    exit 1
    ;;
esac

# First time: generates uv.lock (commit it). Afterwards: installs exactly what the lock says.
SYNC_DEPS='if [ -f uv.lock ]; then uv sync --locked; else uv lock && uv sync; fi'

# Inside a container /.dockerenv exists; on the host there is a Docker CLI.
if [ -f /.dockerenv ] || ! command -v docker >/dev/null 2>&1; then
  echo "▶ [devcontainer] installing dependencies (uv)…"
  sh -c "$SYNC_DEPS"
  echo "✅ Development environment ready."
  exit 0
fi

echo "▶ 1/2  Building and starting the development container…"
$COMPOSE up -d --build --wait
echo "▶ 2/2  Installing dependencies in app-dev (uv)…"
$COMPOSE exec -T app-dev sh -lc "$SYNC_DEPS"
echo "✅ Development environment ready."
