-- =============================================================================
-- 03_grants.sql — Grants + default privileges (idempotente)
-- =============================================================================
-- Matriz completa: docs/architecture/gobernanza-db.md
-- Los dueños (app_owner->app, data_owner->gold/bronze/silver, audit_owner->admin) ya tienen
-- control total por el AUTHORIZATION del schema (02). Aquí otorgamos a los NO-dueños.
-- Principio: empezar desde cero (revoke public) y otorgar EXPLÍCITO. Todo es idempotente.
-- =============================================================================

-- --- 0) Higiene: quitar permisos amplios de PUBLIC ---
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- =============================================================================
-- SCHEMA app  (dueño: app_owner)
-- =============================================================================
GRANT USAGE ON SCHEMA app TO app_user, data_engineer;

-- app_user: DML completo (runtime; sujeto a RLS)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA app TO app_user;
GRANT USAGE, SELECT                  ON ALL SEQUENCES IN SCHEMA app TO app_user;  -- IDs autoincrementales

-- data_engineer: solo lectura de app (para ingerir a bronze)
GRANT SELECT ON ALL TABLES IN SCHEMA app TO data_engineer;

-- Tablas/secuencias FUTURAS heredan permisos solas (las crea app_owner en migraciones)
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app
  GRANT SELECT ON TABLES TO data_engineer;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- =============================================================================
-- SCHEMA gold  (dueño: data_owner) — lo consumen los lectores
-- =============================================================================
GRANT USAGE  ON SCHEMA gold TO read_external, read_internal;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO read_external, read_internal;

-- Objetos FUTUROS de gold heredan SELECT para los lectores
ALTER DEFAULT PRIVILEGES FOR ROLE data_owner IN SCHEMA gold
  GRANT SELECT ON TABLES TO read_external, read_internal;
ALTER DEFAULT PRIVILEGES FOR ROLE data_owner IN SCHEMA gold
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Nota data-team: data_engineer/data_analyst operan el medallion como MIEMBROS de data_owner.
--   Convención: crear objetos con `SET ROLE data_owner` (así el dueño es data_owner y aplica el
--   default-privilege de arriba). El split engineer(bronze/silver)/analyst(gold) es organizacional;
--   para forzarlo por grants, usar membresía NOINHERIT + grants explícitos por capa (variante estricta).

-- =============================================================================
-- SCHEMA bronze / silver (medallion) — descomentar junto con 02
-- =============================================================================
-- GRANT USAGE ON SCHEMA bronze TO data_engineer, data_analyst;
-- GRANT USAGE ON SCHEMA silver TO data_engineer, data_analyst;
-- GRANT SELECT ON ALL TABLES IN SCHEMA silver TO data_analyst;   -- analyst lee silver
--   (data_engineer crea/CRUD en bronze y silver como miembro de data_owner, con SET ROLE data_owner)

-- =============================================================================
-- SCHEMA admin: sin grants a terceros (solo audit_owner por AUTHORIZATION; db_admin superusuario).
-- =============================================================================
