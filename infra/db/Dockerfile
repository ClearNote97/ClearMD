# =============================================================================
# Imagen del servicio `db` — PostgreSQL 18 + extensiones de gobernanza
# -----------------------------------------------------------------------------
# La imagen oficial de Postgres NO incluye pgaudit ni pg_cron. Esta plantilla los
# necesita para la gobernanza (ver docs/architecture/gobernanza-db.md y
# src/database/admin/00_create_extensions.sql), así que se instalan aquí.
#
# Nota: instalar el paquete solo pone la extensión disponible; además hay que:
#   1) precargarla con shared_preload_libraries (se hace en docker-compose.yml → command),
#   2) activarla con CREATE EXTENSION (lo hace 00_create_extensions.sql).
# =============================================================================
FROM postgres:18.4-bookworm

# pgaudit  → auditoría a nivel de sesión/objeto.
# pg_cron  → agendador de tareas dentro de Postgres (mantenimiento, particiones).
# (pg_stat_statements ya viene en la imagen; solo requiere precarga.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-18-pgaudit \
        postgresql-18-cron \
    && rm -rf /var/lib/apt/lists/*
