#!/usr/bin/env bash
# =============================================================================
# run-admin.sh — Idempotent runner for the governance SQL (database/admin/*.sql)
# =============================================================================
# Runs the governance SQL (00_.. 06_) in numeric order, stopping on first error.
# The SQL is idempotent, so re-running is safe.
#
#   Usage:   APP_ENV=dev  ./run-admin.sh      (default)
#            APP_ENV=prod ./run-admin.sh
#
# In DEV you normally DON'T need this: init.sh applies governance by piping the
# SQL into the `db` container. This script is the PROD/CI path, where a `psql`
# client and a directly reachable database exist.
#
# -----------------------------------------------------------------------------
# CONNECTION — one switch: APP_ENV   (this is the part worth learning)
# -----------------------------------------------------------------------------
# The password is ALWAYS read from a secret FILE (never a plaintext value in the
# repo or a shared env var). The only thing that changes dev<->prod is WHERE that
# file lives — decided by APP_ENV, with NO commenting/uncommenting:
#
#   dev  (default): DB_PASSWORD_FILE = ./secrets/db_password.txt  (gitignored, local)
#   prod          : DB_PASSWORD_FILE = /run/secrets/db_password   (mounted by orchestrator/vault)
#
# Override DB_PASSWORD_FILE to point elsewhere. If you prefer, export a ready-made
# DATABASE_URL and it is used as-is (skips the secret-file build).
# =============================================================================
set -euo pipefail

ADMIN_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$ADMIN_DIR/../../.." && pwd)"

# Load .env if present (dev). In prod the orchestrator injects these vars.
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a; . "$PROJECT_ROOT/.env"; set +a
fi

APP_ENV="${APP_ENV:-dev}"

# Default secret location per environment (override DB_PASSWORD_FILE to change it).
# 'prod'/'production' -> prod; anything else (incl. 'development') -> dev.
case "${APP_ENV,,}" in
  prod*) : "${DB_PASSWORD_FILE:=/run/secrets/db_password}" ;;
  *)     : "${DB_PASSWORD_FILE:=$PROJECT_ROOT/secrets/db_password.txt}" ;;
esac

# Connection target:
#   - If DATABASE_URL is set and has no placeholder -> use it verbatim.
#   - Otherwise -> use libpq PG* vars built from parts + the secret file (avoids
#     URL-encoding issues when the password contains special characters).
if [ -n "${DATABASE_URL:-}" ] && ! printf '%s' "$DATABASE_URL" | grep -q 'PASSWORD_HERE'; then
  PSQL_TARGET="$DATABASE_URL"
else
  : "${DB_USER:?DB_USER is required}" "${DB_HOST:?DB_HOST is required}" "${DB_NAME:?DB_NAME is required}"
  [ -f "$DB_PASSWORD_FILE" ] || { echo "secret file not found: $DB_PASSWORD_FILE" >&2; exit 1; }
  export PGHOST="$DB_HOST" PGPORT="${DB_PORT:-5432}" PGUSER="$DB_USER" PGDATABASE="$DB_NAME"
  export PGPASSWORD="$(cat "$DB_PASSWORD_FILE")"
  PSQL_TARGET=""
fi

echo "== admin bootstrap ($APP_ENV): applying governance SQL in order =="
shopt -s nullglob
for f in "$ADMIN_DIR"/[0-9][0-9]_*.sql; do
  echo "---- EXEC: $(basename "$f")"
  psql ${PSQL_TARGET:+"$PSQL_TARGET"} -v ON_ERROR_STOP=1 -f "$f"
done
echo "== admin bootstrap ($APP_ENV): done =="
