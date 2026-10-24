-- =============================================================================
-- 04_rls_policies.sql — RLS: helpers transversales (idempotente)
-- =============================================================================
-- Doc: docs/architecture/multi-tenancy.md
--
-- FRONTERA IMPORTANTE:
--   * Aquí (bootstrap) va SOLO lo transversal e independiente de tablas: el helper de contexto.
--   * Las POLÍTICAS por tabla y el helper de subárbol dependen de `app.tenants` (una tabla de
--     migración) -> viven en la MIGRACIÓN del módulo multi-tenancy (nacen con su tabla).
--   * Multi-tenancy es un MÓDULO: requiere `ltree` + `app.tenants`. Un proyecto mono-tenant lo omite.
--
-- Reglas de oro:
--   * El DUEÑO se salta el RLS -> la app corre como rol NO-dueño (app_user).
--   * "deny by default": al activar RLS, si ninguna política aplica al rol, ve CERO filas.
-- =============================================================================

-- --- Helper transversal: el tenant del contexto de sesión (lo fija la app tras auth) ---
-- No depende de ninguna tabla -> seguro de crear en el bootstrap.
CREATE OR REPLACE FUNCTION admin.current_tenant()
RETURNS uuid
LANGUAGE sql STABLE
AS $$
  SELECT nullif(current_setting('app.current_tenant', true), '')::uuid;
$$;

REVOKE EXECUTE ON FUNCTION admin.current_tenant() FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION admin.current_tenant()
  TO app_user, read_external, read_internal, data_engineer, data_analyst;

-- =============================================================================
-- MÓDULO MULTI-TENANCY — referencia de lo que agrega la MIGRACIÓN (NO se ejecuta aquí)
-- =============================================================================
-- 1) Extensión + tabla del árbol de tenants:
--      CREATE EXTENSION IF NOT EXISTS ltree;
--      CREATE TABLE app.tenants (
--        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--        parent_id uuid REFERENCES app.tenants(id),
--        path ltree NOT NULL,
--        name text NOT NULL
--        -- (+ columnas bitemporales: valid_from/valid_to, recorded_at/superseded_at)
--      );
--      CREATE INDEX ON app.tenants USING gist (path);   -- subárbol rápido
--
-- 2) Helper de subárbol (SECURITY DEFINER: los lectores NO acceden a app.tenants;
--    lee el árbol "en nombre de app_owner" para calcular el subárbol de quien pregunta):
--      CREATE OR REPLACE FUNCTION admin.current_subtree()
--      RETURNS SETOF uuid LANGUAGE sql STABLE
--      SECURITY DEFINER SET search_path = admin, app, pg_temp
--      AS $fn$
--        SELECT t.id FROM app.tenants t
--        WHERE t.path <@ (SELECT path FROM app.tenants WHERE id = admin.current_tenant());
--      $fn$;
--      ALTER FUNCTION admin.current_subtree() OWNER TO app_owner;   -- dueño mínimo, no superusuario
--      REVOKE EXECUTE ON FUNCTION admin.current_subtree() FROM PUBLIC;
--      GRANT  EXECUTE ON FUNCTION admin.current_subtree()
--        TO app_user, read_external, read_internal, data_engineer, data_analyst;
--
-- 3) Política por tabla (en la migración de CADA tabla con tenant):
--    -- operativa (app):
--      ALTER TABLE app.<tabla> ENABLE ROW LEVEL SECURITY;
--      CREATE POLICY <tabla>_subtree ON app.<tabla>
--        USING      (tenant_id IN (SELECT admin.current_subtree()))
--        WITH CHECK (tenant_id IN (SELECT admin.current_subtree()));   -- no insertar para otro tenant
--    -- producto analítico (gold) para externos:
--      ALTER TABLE gold.<tabla> ENABLE ROW LEVEL SECURITY;
--      CREATE POLICY <tabla>_subtree ON gold.<tabla>
--        FOR SELECT USING (tenant_id IN (SELECT admin.current_subtree()));
--      CREATE POLICY <tabla>_internal ON gold.<tabla>       -- exploración cross-tenant (se OR-ea)
--        FOR SELECT TO read_internal USING (true);
--
-- Notas:
--   * data_engineer ve TODO conectándose con app.current_tenant = tenant RAÍZ (subárbol completo). Sin BYPASSRLS.
--   * Máxima estrictez (que ni el dueño se salte el RLS):  ALTER TABLE <t> FORCE ROW LEVEL SECURITY;
-- =============================================================================
