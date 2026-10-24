-- =============================================================================
-- 01_create_roles.sql — Roles (idempotente, SIN contraseñas)
-- =============================================================================
-- Ejecutar como db_admin/superusuario. CREATE ROLE no tiene IF NOT EXISTS -> DO-blocks.
--
-- Principios:
--   * dueño != runtime (la app corre con un rol NO-dueño para que el RLS aplique de verdad).
--   * un dueño "break-glass" por dominio (no todo cae en db_admin).
--   * SIN contraseñas aquí: se asignan al desplegar (ALTER ROLE ... PASSWORD desde un secreto).
--     Un rol LOGIN sin contraseña queda "sellado" hasta que se provisione.
-- =============================================================================

-- db_admin — bootstrap / administración (sellado, break-glass)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'db_admin') THEN
    CREATE ROLE db_admin LOGIN CREATEDB CREATEROLE;
  END IF;
END $$;

-- app_owner — dueño de las tablas de `app`; corre las migraciones (Alembic). NO runtime.
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_owner') THEN
    CREATE ROLE app_owner LOGIN;
  END IF;
END $$;

-- app_user — el rol con el que CORRE la app (DML sobre `app`, sujeto a RLS)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN;
  END IF;
END $$;

-- data_owner — dueño del medallion (bronze/silver/gold); break-glass (sellado, sin uso diario)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'data_owner') THEN
    CREATE ROLE data_owner LOGIN;
  END IF;
END $$;

-- data_engineer — ingesta / refinamiento (app -> bronze -> silver)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'data_engineer') THEN
    CREATE ROLE data_engineer LOGIN;
  END IF;
END $$;

-- data_analyst — analítica (silver -> gold)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'data_analyst') THEN
    CREATE ROLE data_analyst LOGIN;
  END IF;
END $$;

-- read_external — lectura externa (solo gold, tras la API)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'read_external') THEN
    CREATE ROLE read_external LOGIN;
  END IF;
END $$;

-- read_internal — lectura interna (solo gold, exploración directa)
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'read_internal') THEN
    CREATE ROLE read_internal LOGIN;
  END IF;
END $$;

-- audit_owner — "notario" del audit: dueño de fn_audit (SECURITY DEFINER) y de los objetos de admin.
--   NOLOGIN: nadie inicia sesión como el notario; el trigger corre "en su nombre".
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_owner') THEN
    CREATE ROLE audit_owner NOLOGIN;
  END IF;
END $$;

-- --- Membresías: los operadores de datos crean objetos bajo el paraguas de data_owner ---
-- (idempotente: re-otorgar una membresía existente no falla)
GRANT data_owner TO data_engineer;
GRANT data_owner TO data_analyst;

-- =============================================================================
-- Provisión de contraseñas — AL DESPLEGAR, no aquí. Ejemplo (desde Docker secret / vault):
--   ALTER ROLE app_user  PASSWORD '...';
--   ALTER ROLE app_owner PASSWORD '...';
--   -- (data_engineer, data_analyst, read_external, read_internal, según se necesiten)
-- Los break-glass (db_admin, data_owner) y audit_owner (NOLOGIN) quedan sellados por defecto.
-- =============================================================================
