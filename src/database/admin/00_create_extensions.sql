-- =============================================================================
-- 00_create_extensions.sql — Extensiones de PostgreSQL (idempotente)
-- =============================================================================
-- Ejecutar como superusuario/bootstrap (db_admin). Idempotente: CREATE EXTENSION IF NOT EXISTS.
--
-- ⚠️ PRERREQUISITOS DE IMAGEN / SERVIDOR (importante):
--   * pgcrypto ............ viene en la imagen estándar de Postgres (contrib). Directo.
--   * pg_stat_statements .. en contrib, PERO requiere shared_preload_libraries.
--   * pgaudit ............. NO viene en la imagen estándar -> instalar el paquete
--                           postgresql-18-pgaudit en la imagen del servicio `db`, y preload.
--   * pg_cron ............. NO viene en la imagen estándar -> instalar el paquete
--                           postgresql-18-cron, y preload.
--   En postgresql.conf (Dockerfile/compose del servicio db):
--       shared_preload_libraries = 'pg_stat_statements,pgaudit,pg_cron'
--     + reiniciar el servidor.  (Tarea de infra: ver PENDIENTES / capa OPS.)
--
-- NOTA: uuid-ossp NO se instala — gen_random_uuid() es nativo desde PG13.
-- =============================================================================

-- --- Baseline (siempre activas) ---
CREATE EXTENSION IF NOT EXISTS pgcrypto;             -- hashing / cifrado (hash de PII, etc.)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;   -- observabilidad de queries (requiere preload)
CREATE EXTENSION IF NOT EXISTS pgaudit;              -- auditoría de sentencias -> log del servidor (paquete + preload)
CREATE EXTENSION IF NOT EXISTS pg_cron;              -- scheduler dentro de la DB (paquete + preload)

-- --- Menú opcional (descomentar según el proyecto) ---
-- CREATE EXTENSION IF NOT EXISTS ltree;             -- árbol jerárquico de tenants (multi-tenancy)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;           -- búsqueda difusa / acelerar LIKE
-- CREATE EXTENSION IF NOT EXISTS pg_partman;        -- mantenimiento automático de particiones
-- CREATE EXTENSION IF NOT EXISTS postgres_fdw;      -- puente entre bases (Nivel 2)
-- CREATE EXTENSION IF NOT EXISTS pg_graphql;        -- GraphQL nativo (DBaaB, lecturas internas)
-- TimescaleDB: NO es un simple CREATE EXTENSION aquí -> requiere la imagen timescale
--   (ver el servicio `timescaledb` comentado en docker-compose.yml).
