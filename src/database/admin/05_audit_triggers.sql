-- =============================================================================
-- 05_audit_triggers.sql — Trío de audit (idempotente)
-- =============================================================================
-- Ejecutar como SUPERUSUARIO (como 00): usa SET ROLE audit_owner y CREATE EVENT TRIGGER.
-- Doc: docs/architecture/gobernanza-db.md (§ Paso 6)
--
-- Tres registros, tres propósitos (todos en admin, append-only):
--   (a) admin.audit_log        -> cambios de DATOS (app, fila) con PII redactada. Monotemporal.
--   (b) admin.job_run/job_step -> EJECUCIÓN de la analítica (run -> SPs hijos).
--   (c) admin.governance_registry -> cambios de REGLAS (policies/grants/roles). Bitemporal, auto-escrito.
-- Config: admin.pii_columns (bitemporal). Trigger: admin.fn_audit (SECURITY DEFINER, dueño audit_owner).
-- =============================================================================

-- Los objetos de admin quedan en manos de audit_owner (el "notario").
SET ROLE audit_owner;

-- --- Config de PII (bitemporal) ---------------------------------------------
CREATE TABLE IF NOT EXISTS admin.pii_columns (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  schema_name   text NOT NULL,
  table_name    text NOT NULL,
  column_name   text NOT NULL,
  strategy      text NOT NULL CHECK (strategy IN ('omit','mask','hash')),
  valid_from    timestamptz NOT NULL DEFAULT now(),   -- bitemporal: validez
  valid_to      timestamptz,
  recorded_at   timestamptz NOT NULL DEFAULT now(),   -- bitemporal: transacción
  superseded_at timestamptz
);

-- --- (a) audit_log: cambios de datos (particionado por mes) ------------------
CREATE TABLE IF NOT EXISTS admin.audit_log (
  audit_id    bigint GENERATED ALWAYS AS IDENTITY,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  txid        bigint,
  layer       text NOT NULL DEFAULT 'app',
  event_type  text NOT NULL DEFAULT 'row',
  db_role     text,
  app_user_id uuid,
  tenant_id   uuid,
  schema_name text,
  table_name  text,
  operation   text,
  old_data    jsonb,
  new_data    jsonb,
  PRIMARY KEY (audit_id, occurred_at)          -- la PK incluye la clave de partición
) PARTITION BY RANGE (occurred_at);
-- Partición DEFAULT para que los INSERT funcionen desde ya; pg_partman (06) crea las mensuales.
CREATE TABLE IF NOT EXISTS admin.audit_log_default PARTITION OF admin.audit_log DEFAULT;

-- --- (b) job_run / job_step: ejecución de la analítica -----------------------
CREATE TABLE IF NOT EXISTS admin.job_run (
  run_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  layer        text,
  job_name     text NOT NULL,
  started_at   timestamptz NOT NULL DEFAULT now(),
  finished_at  timestamptz,
  status       text NOT NULL DEFAULT 'running',      -- running | success | failed
  triggered_by text                                  -- pg_cron | manual | prefect ...
);
CREATE TABLE IF NOT EXISTS admin.job_step (
  step_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id        bigint NOT NULL REFERENCES admin.job_run(run_id),
  sp_name       text NOT NULL,
  step_order    int,
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  status        text NOT NULL DEFAULT 'running',
  rows_affected bigint,
  error_message text                                 -- el paso que falló salta con su mensaje
);

-- --- (c) governance_registry: cambios de reglas (bitemporal) -----------------
CREATE TABLE IF NOT EXISTS admin.governance_registry (
  registry_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  change_type     text,
  object_identity text,
  command_tag     text,
  actor           text,
  rule_snapshot   jsonb,                             -- TODO: enriquecer del catálogo (pg_policies, etc.)
  valid_from      timestamptz NOT NULL DEFAULT now(),
  valid_to        timestamptz,
  recorded_at     timestamptz NOT NULL DEFAULT now(),
  superseded_at   timestamptz
);

-- --- Redacción de PII: transforma un JSONB según admin.pii_columns -----------
CREATE OR REPLACE FUNCTION admin.redact(data jsonb, p_schema text, p_table text)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $fn$
DECLARE r record; out jsonb := data;
BEGIN
  IF data IS NULL THEN RETURN NULL; END IF;
  FOR r IN
    SELECT column_name, strategy FROM admin.pii_columns
    WHERE schema_name = p_schema AND table_name = p_table AND superseded_at IS NULL  -- versión vigente
  LOOP
    IF out ? r.column_name THEN
      IF    r.strategy = 'omit' THEN out := out - r.column_name;
      ELSIF r.strategy = 'mask' THEN out := jsonb_set(out, ARRAY[r.column_name], '"***"');
      ELSIF r.strategy = 'hash' THEN
        out := jsonb_set(out, ARRAY[r.column_name],
                 to_jsonb('h:' || encode(digest(out ->> r.column_name, 'sha256'), 'hex')));
      END IF;
    END IF;
  END LOOP;
  RETURN out;
END $fn$;

-- --- fn_audit: el trigger de cambios de datos (SECURITY DEFINER = el notario) --
-- INSERT/UPDATE/DELETE a nivel fila. (TRUNCATE necesita un trigger de statement aparte; ver nota.)
CREATE OR REPLACE FUNCTION admin.fn_audit()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = admin, pg_temp AS $fn$
DECLARE v_old jsonb; v_new jsonb;
BEGIN
  IF    TG_OP = 'INSERT' THEN v_new := admin.redact(to_jsonb(NEW), TG_TABLE_SCHEMA, TG_TABLE_NAME);
  ELSIF TG_OP = 'UPDATE' THEN v_old := admin.redact(to_jsonb(OLD), TG_TABLE_SCHEMA, TG_TABLE_NAME);
                              v_new := admin.redact(to_jsonb(NEW), TG_TABLE_SCHEMA, TG_TABLE_NAME);
  ELSIF TG_OP = 'DELETE' THEN v_old := admin.redact(to_jsonb(OLD), TG_TABLE_SCHEMA, TG_TABLE_NAME);
  END IF;

  INSERT INTO admin.audit_log
    (txid, layer, event_type, db_role, app_user_id, tenant_id,
     schema_name, table_name, operation, old_data, new_data)
  VALUES
    (txid_current(), 'app', 'row', session_user,
     nullif(current_setting('app.current_user_id', true), '')::uuid,
     admin.current_tenant(),
     TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP, v_old, v_new);

  RETURN NULL;  -- AFTER trigger
END $fn$;

-- --- Helper para ENCHUFAR el audit a una tabla (idempotente) -----------------
CREATE OR REPLACE FUNCTION admin.enable_audit(p_table regclass)
RETURNS void LANGUAGE plpgsql AS $fn$
BEGIN
  EXECUTE format('DROP TRIGGER IF EXISTS trg_audit ON %s', p_table);
  EXECUTE format('CREATE TRIGGER trg_audit AFTER INSERT OR UPDATE OR DELETE ON %s
                  FOR EACH ROW EXECUTE FUNCTION admin.fn_audit()', p_table);
END $fn$;
-- Uso (en la migración de cada tabla auditada): SELECT admin.enable_audit('app.ventas');

-- --- Captura de gobernanza para el event trigger (SECURITY DEFINER) ----------
CREATE OR REPLACE FUNCTION admin.fn_governance_capture()
RETURNS event_trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = admin, pg_temp AS $fn$
DECLARE r record;
BEGIN
  FOR r IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
    INSERT INTO admin.governance_registry(change_type, object_identity, command_tag, actor)
    VALUES (r.command_tag, r.object_identity, r.command_tag, session_user);
  END LOOP;
END $fn$;

-- --- Vista de "panel único" -------------------------------------------------
CREATE OR REPLACE VIEW admin.v_execution_timeline AS
  SELECT occurred_at AS ts, 'data'::text AS kind, layer,
         schema_name || '.' || table_name AS object, operation AS detail
  FROM admin.audit_log
  UNION ALL
  SELECT started_at, 'job_run', layer, job_name, status FROM admin.job_run
  UNION ALL
  SELECT js.started_at, 'job_step', NULL, js.sp_name, js.status FROM admin.job_step js;

-- Los operadores de datos escriben SU log de ejecución (excepción controlada en admin).
GRANT USAGE ON SCHEMA admin TO data_engineer, data_analyst;
GRANT SELECT, INSERT, UPDATE ON admin.job_run, admin.job_step TO data_engineer, data_analyst;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA admin TO data_engineer, data_analyst;

RESET ROLE;  -- volvemos a superusuario para el event trigger (requiere superusuario)

-- --- Event trigger: auto-escribe governance_registry ------------------------
-- NOTA: los event triggers NO soportan CREATE/ALTER/DROP ROLE (los roles son objetos
-- GLOBALES del clúster, no de la base) → NO pueden ir en WHEN TAG (PostgreSQL lo rechaza:
-- "event triggers are not supported for CREATE ROLE"). Los cambios de rol se registran a
-- mano en admin.governance_registry (o por el proceso que los aplica bajo la regla de 2 aprobadores).
DROP EVENT TRIGGER IF EXISTS trg_governance;
CREATE EVENT TRIGGER trg_governance ON ddl_command_end
  WHEN TAG IN ('CREATE POLICY','ALTER POLICY','DROP POLICY',
               'GRANT','REVOKE','ALTER TABLE')
  EXECUTE FUNCTION admin.fn_governance_capture();

-- =============================================================================
-- Notas / deuda conocida (para no vender humo):
--   * TRUNCATE: fn_audit es FOR EACH ROW (I/U/D). Para auditar TRUNCATE se agrega un trigger
--     FOR EACH STATEMENT aparte (o se registra vía job_step en recargas full de gold).
--   * rule_snapshot: hoy queda NULL; enriquecer leyendo el catálogo (pg_policies/pg_proc) por command_tag.
--   * GRANT/REVOKE no siempre exponen filas en pg_event_trigger_ddl_commands(); su captura puede requerir
--     un manejo específico. El command_tag sí queda registrado.
--   * Bitemporalidad: las columnas están; la lógica de "cerrar la versión previa" (superseded_at/valid_to)
--     se implementa en la migración/proceso que administra cada tabla de estado.
-- =============================================================================
