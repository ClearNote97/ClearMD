#!/usr/bin/env bash
# =============================================================================
# init.sh — Deja el entorno de desarrollo de ClearMD LISTO (idempotente).
# =============================================================================
#   • DENTRO DEL DEVCONTAINER: instala dependencias con uv. Lo dispara el
#     postCreateCommand del devcontainer.
#   • HOST (hay Docker CLI): build + up del contenedor y luego lo mismo dentro.
# ClearMD no usa base de datos (ADR-0002): no hay gobernanza ni migraciones.
# ENTORNO: solo desarrollo. APP_ENV 'prod'/'production' aborta.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose"

# --- Guard de entorno: solo desarrollo ---------------------------------------
APP_ENV="${APP_ENV:-$(grep -E '^APP_ENV=' .env 2>/dev/null | cut -d= -f2- || true)}"
APP_ENV="${APP_ENV:-dev}"
case "${APP_ENV,,}" in
  prod*)
    echo "✋ APP_ENV=$APP_ENV — init.sh es solo para desarrollo." >&2
    exit 1
    ;;
esac

# Primera vez: genera uv.lock (commitéalo). Después: instala exactamente lo del lock.
SYNC_DEPS='if [ -f uv.lock ]; then uv sync --locked; else uv lock && uv sync; fi'

# Dentro de un contenedor existe /.dockerenv; en el host hay Docker CLI.
if [ -f /.dockerenv ] || ! command -v docker >/dev/null 2>&1; then
  echo "▶ [devcontainer] instalando dependencias (uv)…"
  sh -c "$SYNC_DEPS"
  echo "✅ Entorno de desarrollo listo."
  exit 0
fi

echo "▶ 1/2  Construyendo y levantando el contenedor de desarrollo…"
$COMPOSE up -d --build --wait
echo "▶ 2/2  Instalando dependencias en app-dev (uv)…"
$COMPOSE exec -T app-dev sh -lc "$SYNC_DEPS"
echo "✅ Entorno de desarrollo listo."
