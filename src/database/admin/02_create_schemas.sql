-- =============================================================================
-- 02_create_schemas.sql — Schemas (idempotente)
-- =============================================================================
-- Baseline ACTIVO: app (OLTP), admin (gobernanza), gold (consumo analítico).
-- Medallion de refinamiento (bronze/silver): COMENTADO, descomentar al armar la tubería.
-- Cada schema es propiedad del dueño de su dominio (AUTHORIZATION).
-- No usar `public` para tablas de la app (sus permisos se revocan en 03_grants).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS app   AUTHORIZATION app_owner;    -- operativo (OLTP); aquí vive también alembic_version
CREATE SCHEMA IF NOT EXISTS admin AUTHORIZATION audit_owner;  -- gobernanza / auditoría (zona más estricta)
CREATE SCHEMA IF NOT EXISTS gold  AUTHORIZATION data_owner;   -- productos analíticos (superficie de consumo)

-- --- Medallion de refinamiento (descomentar cuando se arme la tubería) ---
-- CREATE SCHEMA IF NOT EXISTS bronze AUTHORIZATION data_owner;  -- crudo (copia de app + ingesta externa)
-- CREATE SCHEMA IF NOT EXISTS silver AUTHORIZATION data_owner;  -- limpio / conformado
