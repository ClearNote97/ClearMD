#!/usr/bin/env bash
# =============================================================================
# init.sh — Deja el entorno de desarrollo LISTO (idempotente). AUTODETECTA modo:
# =============================================================================
#   • HOST (hay Docker CLI): build + up + (si hay DB) gobernanza + deps + (si hay DB) migraciones.
#   • DENTRO DEL DEVCONTAINER (sin Docker CLI): deps + (si hay DB) gobernanza + migraciones.
# El modo se autodetecta. En dev, lo dispara el `postCreateCommand` del devcontainer.
# La DB es OPCIONAL: si no hay una alcanzable (COMPOSE_PROFILES sin 'db', o un proyecto
# sin base de datos), se OMITEN gobernanza y migraciones automáticamente — sin tocar nada.
#
# ENTORNO: solo desarrollo. Lo decide APP_ENV (dev por defecto; 'prod'/'production'
#   aborta). En prod la gobernanza se aplica con:
#     APP_ENV=prod ./src/database/admin/run-admin.sh
#
# SEEDS: los de datos (dependientes de tablas de Alembic) van DESPUÉS de las
#   migraciones (ver bloque comentado). Los de DDL previa, por el entrypoint de Postgres.
#
# Estado 0 → N: en un proyecto nuevo, el paso de deps GENERA pyproject.toml + uv.lock
#   (commitéalos). Para dejar la plantilla prístina tras una prueba:
#     docker compose down -v && git clean -fx pyproject.toml uv.lock
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose"

# --- Guard de entorno: solo desarrollo ---------------------------------------
# APP_ENV del shell o del .env; por defecto "dev". 'prod'/'production' → aborta.
APP_ENV="${APP_ENV:-$(grep -E '^APP_ENV=' .env 2>/dev/null | cut -d= -f2- || true)}"
APP_ENV="${APP_ENV:-dev}"
case "${APP_ENV,,}" in
  prod*)
    echo "✋ APP_ENV=$APP_ENV — init.sh es solo para desarrollo." >&2
    echo "   En prod: despliega con tu orquestador y aplica la gobernanza con:" >&2
    echo "     APP_ENV=prod ./src/database/admin/run-admin.sh" >&2
    exit 1
    ;;
esac

# --- Deps de Python con uv (Estado 0/N) — se usa dentro del contenedor --------
deps_uv() {
  if [ -f pyproject.toml ] && [ -f uv.lock ]; then
    uv sync --locked
  elif [ -f pyproject.toml ]; then
    uv lock && uv sync
  elif [ -f requirements.txt ]; then
    uv init --no-package --no-workspace . && rm -f main.py && uv add -r requirements.txt
  else
    echo "Sin requirements.txt ni pyproject.toml: nada que instalar."
  fi
}

# --- ¿Este proyecto tiene DB activa? (auto-detección) ------------------------
# Responde a: servicio `db` comentado/eliminado, profile "db" apagado
# (COMPOSE_PROFILES sin 'db'), o DB no levantada. Si no hay DB, se saltan
# gobernanza y migraciones — el "modo sin DB" no exige tocar este script.
uses_db() {
  if [ -f /.dockerenv ] || ! command -v docker >/dev/null 2>&1; then
    # DEVCONTAINER: probamos el puerto de la DB (host:port del .env), resoluble por
    # la red interna de Docker. Sin respuesta → no hay DB.
    local h p
    h="$(grep -E '^DB_HOST=' .env 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"; h="${h:-db}"
    p="$(grep -E '^DB_PORT=' .env 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"; p="${p:-5432}"
    timeout 3 bash -c ">/dev/tcp/$h/$p" 2>/dev/null
  else
    # HOST: ¿hay un contenedor del servicio 'db' en marcha?
    [ -n "$($COMPOSE ps -q db 2>/dev/null)" ]
  fi
}

# --- Autodetección de contexto -----------------------------------------------
# Dentro de un contenedor existe /.dockerenv; en el host hay Docker CLI.
if [ -f /.dockerenv ] || ! command -v docker >/dev/null 2>&1; then
  # ===== MODO DEVCONTAINER =====  (no hay Docker CLI; VS Code ya levantó lo que toque)
  echo "▶ [devcontainer] preparando entorno…"
  echo "  • Dependencias (uv)…";          deps_uv
  if uses_db; then
    echo "  • Gobernanza (admin)…";       ./src/database/admin/run-admin.sh
    echo "  • Migraciones (alembic)…";    uv run alembic upgrade head
  else
    echo "  • Sin DB → se omiten gobernanza y migraciones (proyecto sin base de datos)."
  fi
  echo "✅ Entorno de desarrollo listo (modo devcontainer)."
  exit 0
fi

# ===== MODO HOST =====  (orquestación completa)
echo "▶ 1/4  Construyendo imágenes y levantando servicios (espera DB sana)…"
$COMPOSE up -d --build --wait

if uses_db; then
  echo "▶ 2/4  Aplicando gobernanza (admin/00..06) en la base de datos…"
  for f in src/database/admin/[0-9][0-9]_*.sql; do
    echo "     • $(basename "$f")"
    # ON_ERROR_STOP=1 → psql sale con error y `set -e` aborta el bootstrap.
    $COMPOSE exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' < "$f"
  done
else
  echo "▶ 2/4  Sin DB (profile 'db' apagado) → se omite la gobernanza."
fi

echo "▶ 3/4  Preparando dependencias de Python en app-dev (uv)…"
$COMPOSE exec -T app-dev sh -lc '
  if [ -f pyproject.toml ] && [ -f uv.lock ]; then
    uv sync --locked
  elif [ -f pyproject.toml ]; then
    uv lock && uv sync
  elif [ -f requirements.txt ]; then
    uv init --no-package --no-workspace . && rm -f main.py && uv add -r requirements.txt
  fi'

if uses_db; then
  echo "▶ 4/4  Aplicando migraciones (alembic upgrade head)…"
  $COMPOSE exec -T app-dev sh -lc 'uv run alembic upgrade head'
else
  echo "▶ 4/4  Sin DB → se omiten las migraciones."
fi

# ── (opcional) SEEDS de DATOS, DESPUÉS de migraciones ────────────────────────
# Para datos que dependan de tablas creadas por Alembic. Antes de activar, quita el
# montaje `./data/seeds:/docker-entrypoint-initdb.d` del compose (evita doble corrida).
# for f in data/seeds/*.sql; do
#   [ -e "$f" ] || continue
#   $COMPOSE exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' < "$f"
# done

echo
echo "✅ Base de datos lista. Estado de los servicios:"
$COMPOSE ps
