# 🏛️ Gobernanza de la base de datos — diseño (proceso vivo)

> **Doc de trabajo.** Construimos la gobernanza de PostgreSQL **paso a paso**, de lo general a lo específico,
> hasta consolidar la documentación de la plantilla. Este archivo **se consolida en su lugar**: hoy es el
> proceso de diseño; al terminar, es *la* doc de arquitectura de la gobernanza.
>
> - Plano maestro (spec de la gobernanza): [`../../src/database/admin/admin-manifest.yaml`](../../src/database/admin/admin-manifest.yaml)
> - El *por qué* de fondo: `ACUERDOS_CLEARNOTE_DEV.md` (raíz de Plantillas)

## El "deber ser" de la gobernanza (marco)

| Cualidad | Qué significa |
|---|---|
| Segura por defecto | secrets fuera del repo, **mínimo privilegio**, auditoría |
| Gobernada | roles, schemas, RLS, migraciones ordenadas e idempotentes |
| Dueño ≠ runtime | quien **posee/migra** (DDL) es distinto de quien **corre la app** (DML) → el RLS es real |
| Bootstrap claro | camino clone → DB arriba → gobernanza aplicada → app conecta |
| Agnóstica | sin rastros de cliente; el molde no trae datos de un proyecto concreto |

## Mejoras al manifest (acordadas)

1. Renombrar `3_grants.sql` → `03_grants.sql` (arregla el orden del runner: `"3_"` ordena tras `"06_"`).
2. Declarar la frontera **`admin/` (bootstrap, una vez) ↔ `migrations/` (Alembic, evolución continua)**.
3. Codificar el gotcha de **RLS**: el dueño de la tabla la salta → la app corre con rol **no-dueño**.
4. Codificar *idioms* de **idempotencia** por tipo de objeto (extensión `IF NOT EXISTS`, función `CREATE OR REPLACE`, rol `DO`-block).
5. **Higiene de plantilla:** genericizar `meta` (owner/fecha) y volver `related_spec_reference` un ejemplo genérico (sin dominio salud).

## Plan paso a paso (general → específico)

1. **Modelo de roles** (incl. `app_user`) ← ✅ CERRADO
2. Schemas ← ✅ CERRADO
3. Extensiones (base técnica) ← ✅ CERRADO
4. Grants + modelo de roles final ← ✅ CERRADO
5. RLS + multi-tenancy jerárquico ← ✅ CERRADO (doc: `multi-tenancy.md`)
6. Audit (`audit_log` + `job_run/step` + `governance_registry`) ← ✅ CERRADO
7. Maintenance (pg_cron, pg_partman/retención, autovacuum/ANALYZE, logs OPS) ← ✅ CERRADO
8. Consolidar: manifest v2 + `run-admin.sh` + entorno Alembic (`env.py`, `script.py.mako`, `alembic.ini`) ← ✅ CERRADO
9. **Ejecución: los 7 `.sql` de `admin/` ESCRITOS** (00-06) ← ✅ (falta: imagen del `db` con pgaudit/pg_cron + `shared_preload_libraries`; probarlos en un Postgres real)

## Paso 1 — Modelo de roles ✅

Principio raíz: **dueño ≠ runtime** + **mínimo privilegio**. Cinco roles concretos:

| Rol | ¿LOGIN? | Para qué | Privilegios | ¿Dueño? | ¿RLS aplica? |
|---|---|---|---|---|---|
| `db_admin` | solo bootstrap | correr los SQL de `admin/` (extensiones/roles/schemas) | alto (superusuario de arranque) | — | N/A |
| `app_owner` | solo migraciones | **posee** schemas/tablas; corre Alembic (DDL) | DDL sobre el schema de la app | **sí** | no (dueño → la salta) |
| `app_user` | **sí (runtime)** | el rol con el que **corre la app** | DML sobre el schema app | no | **sí** |
| `analytics` | sí | BI / ML / notebooks | read en `canonical`/`analytics` (+ write en `analytics`) | no | sí |
| `readonly` | sí | reportería / lectura externa | solo SELECT | no | sí |

**Principios escritos junto a los roles:**
- **Dueño ≠ runtime:** `app_owner` posee y migra; `app_user` corre la app → el RLS es real. La app **nunca** corre como dueño.
- **Ciclo:** `app_owner` actúa en setup + migraciones (DDL); `app_user` en cada request (DML), sin DDL.
- **Seguridad:** correr como `app_user` (solo DML, RLS activo, sin DDL) **limita el blast radius** ante bug/inyección.
- **Default privileges** (`ALTER DEFAULT PRIVILEGES`) para que los objetos **futuros** hereden permisos solos.
- **Sin passwords en el repo:** roles creados sin contraseña; se asigna al desplegar (Docker secrets/vault). Idempotencia con bloque `DO` (`CREATE ROLE` no tiene `IF NOT EXISTS`).

### Mejora futura (documentada, NO implementada): roles de grupo + login
Patrón "pro" para escalar: roles **`NOLOGIN`** que guardan los privilegios (grupos por función:
`grp_app_rw`, `grp_readonly`, …) + roles **`LOGIN`** que son **miembros** y heredan. Ventaja: gestionas los
privilegios **una sola vez** en el grupo, y agregar/quitar usuarios es cambiar membresías. Hoy usamos los 5
roles concretos (más simples); este patrón queda como camino de mejora cuando haya muchos usuarios/roles.

## Paso 2 — Schemas ✅

**Nomenclatura estándar medallion** (bronze/silver/gold) en vez de landing/raw/canonical; `gold` **absorbe** el
viejo `analytics`. Unifica los dos flujos (copia interna `app`→bronze + ingesta externa) en un solo pipeline.

| Schema | Contenido | Capa |
|---|---|---|
| `app` | operativo / **OLTP** (caliente) | operacional |
| `admin` | gobernanza / auditoría | operacional |
| `bronze` | dato crudo (copia point-in-time de `app` + ingesta externa) | analítica |
| `silver` | limpio / conformado | analítica |
| `gold` | agregados de negocio (lo que leen dashboards) — **reemplaza `analytics`** | analítica |

**Principio — lógico ≠ físico:** los schemas son el diseño **lógico**; los Niveles 1/2/3 son **dónde viven** (topología física):
- **Nivel 1:** todos los schemas en **una** base → ETL `app`→bronze trivial (in-DB / mat. view), JOIN libre.
- **Nivel 2:** **dos bases** (mismo servidor) cortando por la costura **operacional `(app+admin)` | analítica `(bronze/silver/gold)`** →
  el ETL cruza frontera → **`postgres_fdw`** o pipeline. `admin` viaja con lo operacional.
- **Nivel 3:** servidores separados.
- **Diseñar para la costura:** el acceso analítico pasa por `repositories`/`session` → saltar 1→2 = cambiar la conexión, no rediseñar.

**El "ETL" liviano (Nivel 1):** materialized views + `pg_cron`; pipelines complejos → Prefect (servicio opcional del compose).
**No usar `public`** para tablas de la app.

**Decidido:** medallion **completo documentado**; el **baseline EJECUTA `app`+`admin`+`gold`** (`bronze`/`silver`
van **comentados** en `02_create_schemas.sql`, listos para descomentar cuando se arme el pipeline).

### Gobernanza de acceso (pre-diseña Pasos 4 grants y 6 audit)

**Distinción clave:** control de acceso (quién ve/hace qué) = **schemas + grants, ya en Nivel 1**. La separación
física (bases/servidores) = aislamiento/rendimiento, Nivel 2/3. Las reglas de roles **NO** necesitan Nivel 2.

**Matriz de grants (baseline, Nivel 1):**

| Rol | `app` | `bronze/silver/gold` | `admin` |
|---|---|---|---|
| `app_owner` | dueño (DDL) | — (o lectura) | — |
| `app_user` | DML | — | — (audita vía trigger) |
| `analytics` | solo lectura | RW | — |
| `readonly` | solo lectura | lectura (`gold`) | — |
| `db_admin` / `audit` | — | — | **único con acceso** |

**Audit sin dar acceso a `admin`:** trigger **`SECURITY DEFINER`** (corre con privilegios de su dueño, p. ej.
`audit_owner`) → `app_user` queda **auditado sin tener ningún grant** sobre `admin` (no puede leer ni borrar su rastro).

**`admin` = zona más estricta.** En Nivel 2+ puede separarse **físicamente** (corte de 3 zonas: operacional |
analítica | admin) como *defense in depth*: ni un superusuario comprometido de la base operativa borra la auditoría.

## Paso 3 — Extensiones ✅

**Baseline activo** (en `00_create_extensions.sql`): `pgcrypto` (crypto/hash) · `pg_stat_statements` (observabilidad) ·
`pg_cron` (scheduler ETL/maintenance) · **`pgaudit`** (auditoría a nivel **sentencia** — complementa el audit por trigger).

**Menú condicional (comentado, con su nota):**
- `pg_trgm` — búsqueda difusa **vía ORM** (índice GIN trigram en migración + `func.similarity`).
- `ltree` — **árbol de tenants** (multi-tenancy jerárquico); consultas de subárbol rápidas (GiST). Ver `multi-tenancy.md`.
- `pg_partman` — particiones automáticas; capa **admin/maintenance** (pg_cron), **NO** app.
- `postgres_fdw` — Nivel 2 (puente entre bases).
- `pg_graphql` — DBaaB (ver decisión de arquitectura).
- `timescaledb` — series de tiempo (cambia la imagen base; servicio alterno del compose).
- FTS nativo (`tsvector`) disponible; BM25 (`pg_search`) emergente → validar.

**Fuera de las extensiones:** `uuid-ossp` **quitada** (`gen_random_uuid()` nativo PG13+) · `pglogical` → preferir
replicación **nativa** (PG10+), avanzado · **pgBackRest** → herramienta de **ops** (backup/PITR), no extensión ·
`file_fdw` **descartada**: la ingesta de archivos de clientes es un **módulo de app** (`use_case` → valida → carga a `bronze`), no file_fdw.

## Paso 4 — Grants + modelo de roles FINAL ✅

> Este modelo **expande y reemplaza** el bosquejo inicial de 5 roles del Paso 1. **9 roles**, un dueño de
> emergencia por dominio (no todo cae en `db_admin`).

**Notación:** OWNER = dueño/DDL · CREATE+CRUD = crea objetos + DML · CRUD = DML · R = SELECT · — = nada.

| Rol | `app` | `bronze` | `silver` | `gold` | `admin` | Uso |
|---|---|---|---|---|---|---|
| `db_admin` | crea extensiones/roles/schemas (bootstrap) | — | — | — | — | 🔒 bootstrap |
| `app_owner` | OWNER | — | — | — | — | migraciones app |
| `app_user` | CRUD | — | — | — | — \* | runtime app |
| `data_owner` | — | OWNER | OWNER | OWNER | — | 🔒 break-glass |
| `data_engineer` | R | CREATE+CRUD | CREATE+CRUD | — | — | ingesta/refinamiento |
| `data_analyst` | — | — | R | CREATE+CRUD | — | analítica |
| `read_external` | — | — | — | R | — | externo (tras API) |
| `read_internal` | — | — | — | R | — | interno (exploración) |
| `audit_owner` | — | — | — | — | OWNER | notario del audit |

\* `app_user` sin acceso a `admin`; auditado vía trigger `SECURITY DEFINER`.

**Dueño de emergencia por dominio (break-glass):** app→`app_owner`, data→`data_owner`, admin→`audit_owner`,
bootstrap→`db_admin`. Los dueños poderosos van **sellados**; el día a día usa los operadores acotados.
`data_engineer`/`data_analyst` son **miembros** de `data_owner` y crean objetos con `SET ROLE data_owner`
(para que en emergencia `data_owner` los administre).

**`read_external` vs `read_internal`:** mismo grant base (`gold` R); se diferencian en **RLS/acceso** (Paso 5).
**`gold` = única superficie de consumo**: si el interno necesita datos crudos, se **copian a `gold`**, no se abre `silver`.

**Idioms de grants (van en `03_grants.sql`):**
- `REVOKE ALL ON SCHEMA public FROM PUBLIC` — empezar desde cero, otorgar explícito.
- `GRANT USAGE ON SCHEMA ...` + privilegios de tabla por rol (según la matriz).
- 🔑 `ALTER DEFAULT PRIVILEGES FOR ROLE <dueño> IN SCHEMA ...` — que las tablas **futuras** hereden permisos solas.
- **Secuencias:** `GRANT USAGE ON ... SEQUENCES` (si no, el `INSERT` con id autoincremental falla).
- **Funciones:** `REVOKE EXECUTE ... FROM PUBLIC` y otorgar explícito.
- **Pendiente Paso 5:** `data_engineer` quizá necesite `BYPASSRLS` para copiar `app`→`bronze` completo.

## Decisión de arquitectura — DBaaB por frontera de confianza

**Columna = arquitectura limpia** (`use_cases` dueños de la lógica). El "DB as a Backend" se adopta **solo en un borde**,
cortando por la **frontera de confianza** (no por read/write):
- **Interno** (módulos, tableros, productos propios) → **DBaaB**: `pg_graphql`/PostgREST sobre `gold` (lectura flexible, bajo boilerplate; RLS autoriza).
- **Externo** (terceros, integraciones) → **API propia (FastAPI) con su contrato** (`spec/contracts/`). **Nunca** exponer el schema de la DB afuera (estabilidad de contrato, seguridad, desacople).
- Grupo A de extensiones = superpoderes internos (vía ORM/migraciones), neutrales a la arquitectura.
- `pg_partman` + pgBackRest = capa **admin/ops** (DB/infra), nunca la app.

## Paso 6 — Audit (en curso)

**Tres patas:** trigger `fn_audit`→`admin.audit_log` (cambios de datos) · `pgaudit` (sentencias→log del servidor) ·
event trigger→`admin.governance_registry` (cambios de las reglas, **bitemporal**).

### Esquema `admin.audit_log` ✅ (append-only, INMUTABLE, particionada por `occurred_at`)

| Columna | Tipo | Qué |
|---|---|---|
| `audit_id` | bigint/uuid | id del evento |
| `occurred_at` | timestamptz | cuándo (clave de partición) |
| `txid` | bigint | agrupa la transacción |
| `db_role` | text | rol DB (`session_user`) |
| `app_user_id` | uuid | usuario REAL (`app.current_user_id`) |
| `tenant_id` | uuid | tenant (`app.current_tenant`) |
| `schema_name`/`table_name` | text | qué objeto |
| `operation` | text | INSERT/UPDATE/DELETE/TRUNCATE |
| `row_pk` | jsonb | PK de la fila |
| `old_data`/`new_data` | jsonb | antes/después (PII redactada) |

- **Inmutable:** solo el trigger (como `audit_owner`, SECURITY DEFINER) inserta; nadie UPDATE/DELETE; lectura solo `audit_owner`/`db_admin`.
- **NO bitemporal** (log de eventos append-only, monotemporal); lo bitemporal es `governance_registry`.

### El "quién" real ✅ — convención de contexto de sesión
La app fija **por request** (y esto sirve para RLS **y** audit):
`SET LOCAL app.current_tenant = ...` + `SET LOCAL app.current_user_id = ...`.
El trigger lee `current_setting('app.current_user_id', true)`, `current_setting('app.current_tenant', true)`, `session_user`.
→ **Una convención, dos usos:** RLS (qué ves) + audit (quién fuiste).

### Familia de audit ✅ — dos propósitos, tablas dedicadas
- **`admin.audit_log`** — cambios de **DATOS** (`app`, fila-por-fila): I/U/D/TRUNCATE; `old_data`/`new_data` fila
  completa (PII redactada) + `changed_fields` opcional; campo `layer`. (U/D serán raras por diseño.)
- **`admin.job_run`** + **`admin.job_step`** — **EJECUCIÓN** de la analítica (bronze/silver/gold). Patrón
  *1 job → SP orquestador → SPs hijos*: `job_run` (corrida) padre de `job_step` (cada SP: `status`,
  `rows_affected`, `error_message`) → **pinpoint del paso que falló**. Consistente con §9 (EN_CURSO/EXITO/FALLO).
- **Vista `admin.v_execution_timeline`** — une audit_log + job_run + job_step (el "panel único" sin forzar una sola tabla).
- Todo en `admin`, append-only, monotemporal.

### Alcance / operaciones / formato / PII ✅
- **Alcance:** `app`→`audit_log` (row); `bronze/silver/gold`→`job_run`/`job_step`; `admin`→`governance_registry` (no se auto-audita).
- **Operaciones (row):** I/U/D + TRUNCATE. SELECT → `pgaudit`.
- **Formato:** fila completa `old`/`new` JSONB + `changed_fields` opcional.
- **PII:** `admin.pii_columns(schema, table, column, strategy: omit|mask|hash)`, **bitemporal**. El trigger redacta al armar el JSONB.

### Identidad y anonimización (patrón de app, complementario a PII) ✅
- **`person_id` surrogate** estable + **documentos versionados** (bitemporal, ej. RC→TI→CC). Analítica/audit usan el
  surrogate (anónimo); el PII real queda aislado en `app` + redactado.
- **Convención de arranque:** al iniciar desarrollo, modelar la **identidad de los actores** (personas/clientes/empleados/proveedores)
  + qué necesita **trazabilidad PII bitemporal**. (Junto a la regla "¿va bitemporal?" por tabla.)

### `admin.governance_registry` ✅ — libro mayor de las REGLAS (bitemporal, auto-escrito)
- Audita las **reglas** (no los datos): `CREATE/ALTER/DROP POLICY`, `ENABLE/DISABLE RLS`, `GRANT/REVOKE`, `CREATE/ALTER ROLE`, ownership.
- **Auto-poblado por un EVENT TRIGGER** DDL (`ddl_command_end`) → no se puede olvidar registrar una regla.
- Columnas: `registry_id`, `change_type`, `object`, `command_tag`, `actor`, `rule_snapshot` (jsonb leído del catálogo),
  `valid_from`/`valid_to` + `recorded_at`/`superseded_at` (**bitemporal**).
- **Limitación honesta:** el event trigger da comando + objeto; la definición completa se guarda como `rule_snapshot`
  (consultado de `pg_policies`, etc. al capturar). **NO hace enforcement** (las políticas viven pegadas a sus tablas) — es **visibilidad**.

### ⭐ Buena práctica destacada — Regla de 2 aprobadores ✅
> **Todo cambio que DESACTIVE o ALTERE RLS o audit requiere DOS aprobadores humanos.**
- Es regla de **proceso**, no mecanismo de DB.
- Se **enforcea en el repo** (branch protection + `CODEOWNERS` sobre `admin/`, RLS y audit), **no** en Postgres.
- **Es una buena práctica *sugerida* de la plantilla** → se eleva al **manifest** (Paso 8) y a **`spec/constitution/01_principles.md`**.

**Paso 6 CERRADO** ✅ — tres registros, tres propósitos: `audit_log` (datos), `job_run/step` (ejecución), `governance_registry` (reglas).

## Paso 7 — Maintenance ✅

Todo el SQL vive en `06_maintenance.sql` (bootstrap admin).

- **`pg_cron`** (requiere `shared_preload_libraries='pg_cron'` en el server → `Dockerfile`/`compose`): agenda el
  **refresh de la analítica** (job orquestador → `job_run/step`; default nocturno, configurable), el **mantenimiento de
  `pg_partman`** y **housekeeping** (`ANALYZE`, refresh de vistas). Cada job corre **con su rol** (refresh=`data_engineer`/`data_analyst`; particiones=dueño).
- **`pg_partman` + retención:** `audit_log` particionada mensual (crea las futuras, purga las viejas con `DROP` de partición).
  Retención por defecto (la fija **compliance**): `audit_log` ~**24m**, `job_run/step` ~**90d**. La **redacción de PII habilita retención larga** sin riesgo de privacidad.
- **Autovacuum + `ANALYZE`:** autovacuum hace el grueso; **`ANALYZE` explícito tras recargas full de `gold`** (stats frescas → tablero rápido); afinar umbrales en tablas calientes (`audit_log`) si hace falta.
- **Logs fuera de la DB → OPS** (ver abajo).

## Recordatorio — logs (dos mundos) [para Paso 7 / capa OPS]

- **Dentro de la DB:** `admin.audit_log` → mantenimiento con **pg_partman + retención** (Paso 7).
- **Fuera de la DB (OPS):** log del **servidor Postgres** (incl. **`pgaudit`** y slow queries), log de la **app** (Python),
  logs de **contenedores** (db/app/nginx), **nginx**. Se tratan con: **rotación** (tamaño/tiempo + comprimir),
  **retención** (30/90 días según compliance), **nivel** (prod ≠ `DEBUG`), y opcional **agregación** (Loki/ELK).
- **Dónde vive:** capa **OPS/despliegue** (`docker-compose` logging drivers, config nginx/postgres) — hermano de pgBackRest, NO gobernanza de DB. Se detalla al tocar el compose.

## Decisiones cerradas
- **[Paso 1] Modelo de roles:** 5 roles concretos (`db_admin`, `app_owner`, `app_user`, `analytics`, `readonly`),
  principio dueño≠runtime, default privileges, sin passwords en repo. Patrón grupo+login documentado para el futuro.
- **[Paso 2] Schemas:** nomenclatura **bronze/silver/gold** (estándar; `gold` absorbe `analytics`).
  Operacional=`app`+`admin`, analítica=medallion. **Escalera = misma lógica, distinta ubicación física**
  (Nivel 1 una base → Nivel 2 dos bases cortando por operacional|analítica con `postgres_fdw` → Nivel 3 servidores).
  Diseñar detrás de `repositories`/`session` para que el salto 1→2 sea cambiar conexión. No usar `public`.
  `analytics` = copia point-in-time de `app` vía ETL (mat. views+pg_cron, o Prefect). Granularidad de baseline: pendiente.
- **[Gobernanza de acceso]** Control de acceso por **grants en Nivel 1** (≠ separación física). Matriz definida
  (`app_owner`/`app_user`/`analytics`/`readonly`/`admin`); audit vía trigger **`SECURITY DEFINER`** (app roles con
  cero acceso a `admin`); `admin` separable físicamente en Nivel 2+ (3 zonas) para integridad de auditoría. Pre-diseña Pasos 4 y 6.
- **[Paso 3] Extensiones:** baseline `pgcrypto`+`pg_stat_statements`+`pg_cron`+**`pgaudit`**; menú condicional comentado
  (pg_trgm, pg_partman, postgres_fdw, pg_graphql, timescaledb, FTS/BM25). Quitar `uuid-ossp`; `pglogical`→nativa; pgBackRest=ops; `file_fdw` descartada (ingesta = módulo de app).
- **[Arquitectura] DBaaB por frontera de confianza:** arquitectura limpia de base; **interno = DBaaB** (`pg_graphql` sobre `gold`),
  **externo = API propia (FastAPI) con contrato**. Nunca exponer el schema afuera. `pg_partman`+pgBackRest = admin/ops.
- **[Gobernanza — bitemporalidad]** Convención `bitemporal-by-design` **acotada** a tablas de **gobernanza / estado / referencia**
  (NO operativas de alta rotación). **Regla dura:** al crear una tabla de ese tipo, parada obligatoria "¿va bitemporal?" con
  argumentos a favor/en contra. Implementación: columnas `valid_from/valid_to`+`recorded_at/superseded_at` + triggers de
  versionado + vistas "current"; se junta con pg_partman + retención por el volumen.
- **[Gobernanza — registry]** `admin.governance_registry` **bitemporal**, **auto-poblado por un EVENT TRIGGER** DDL
  (captura `CREATE POLICY`/`GRANT`/cambios de gobernanza) → libro mayor único, auto-escrito, time-travel-able. No hace
  enforcement (eso lo hacen las políticas pegadas a sus tablas); da el **panel único** de visibilidad.
- **[Paso 4] Grants + roles (FINAL, 9 roles):** `db_admin`/`app_owner`/`app_user`/`data_owner`/`data_engineer`/`data_analyst`/`read_external`/`read_internal`/`audit_owner`.
  Un dueño break-glass por dominio; operadores acotados en el día a día. `REVOKE public` + `ALTER DEFAULT PRIVILEGES` + secuencias/funciones.
  `read_ext`≠`read_int` por RLS/acceso (mismo grant base). `data_engineer` posible `BYPASSRLS` (Paso 5).
- **[Paso 5] RLS + multi-tenancy JERÁRQUICO** (doc propio: [`multi-tenancy.md`](./multi-tenancy.md)): **árbol de tenants**
  (`app.tenants` bitemporal, `ltree`); **una sola** política de subárbol en `app`+`gold`; identidad por `SET LOCAL app.current_tenant`.
  **Rol = capacidad/vía; posición en el árbol = alcance.** `read_external`(API)/`read_internal`(directo) separados por vía
  (retroalimenta, no sustituye). `data_engineer` en **posición raíz** → ve todo por la misma política (**sin `BYPASSRLS`**).
  Módulo habilitable (mono-tenant lo omite).
- **[Paso 6] Audit — tres registros:** `admin.audit_log` (cambios de **datos** en `app`, fila, monotemporal, PII redactada vía
  `admin.pii_columns` omit/mask/hash bitemporal) + `admin.job_run`/`admin.job_step` (**ejecución** analítica run→step,
  pinpoint del paso fallido) + vista unificadora `v_execution_timeline`. Trigger `fn_audit` `SECURITY DEFINER`; "quién" real
  vía `app.current_user_id`/`app.current_tenant`. Identidad: `person_id` surrogate + documentos versionados (bitemporal) → anonimización por diseño.
- **[Paso 6] `governance_registry`:** libro mayor **bitemporal** de las reglas, **auto-escrito por event trigger** DDL
  (policies/grants/roles), con `rule_snapshot`; solo visibilidad, no enforcement.
- **[⭐ Buena práctica] Regla de 2 aprobadores:** desactivar/alterar RLS o audit ⇒ 2 aprobadores humanos; enforce en el
  repo (branch protection + CODEOWNERS). Se eleva a manifest + `01_principles.md`. **Buena práctica sugerida de la plantilla.**
- **[Convenciones de arranque]** al iniciar desarrollo: (a) "¿esta tabla va bitemporal?" (estado/referencia/gobernanza);
  (b) modelar identidad de los actores + trazabilidad PII bitemporal.
- **[Paso 7] Maintenance:** `pg_cron` (agenda refresh + partman + housekeeping, cada job con su rol; requiere
  `shared_preload_libraries`) · `pg_partman` + retención (audit ~24m / ejecución ~90d, configurable por compliance;
  la redacción PII habilita retención larga) · autovacuum + `ANALYZE` post-recarga full de `gold` · logs OPS aparte. Todo en `06_maintenance.sql`.
- **[Paso 8] Consolidar — ARTEFACTOS ESCRITOS:** `admin-manifest.yaml` v2 (agnóstico, con los principios, los 7 archivos,
  CI checks incl. 2-aprobadores, secrets dev/prod) · `run-admin.sh` (idempotente, orden `[0-9][0-9]_*.sql`, `ON_ERROR_STOP`,
  conexión decidida por **`APP_ENV`** — secreto por archivo en dev/prod, sin comentar/descomentar) · entorno Alembic
  (`alembic.ini` sin URL en claro, `env.py` resuelve la URL vía **`connection.py`** — la MISMA que la app —
  `SQLModel.metadata` + `version_table_schema='app'`, `script.py.mako`). Renombrado `3_grants.sql`→`03_grants.sql`.
  **Baseline:** medallion completo documentado, ejecuta `app`+`admin`+`gold` (bronze/silver comentados).
- **[Arranque] `init.sh` raíz (dev):** build+up+`--wait` → gobernanza (SQL canalizado al contenedor `db`) → deps `uv` →
  `alembic upgrade head`. Todo gira sobre **`APP_ENV`** (`connection.py` = fuente única de conexión y secretos; `init.sh` solo dev).
- **[Ejecución] Los 7 `.sql` de `admin/` ESCRITOS** (00 extensiones · 01 roles/DO-blocks · 02 schemas · 03 grants+default privileges ·
  04 RLS helper transversal + patrón multi-tenancy · 05 trío de audit + PII + event trigger · 06 maintenance/recetario). 522 líneas.
  **Pendiente real:** imagen del servicio `db` con paquetes `pgaudit`/`pg_cron` + `shared_preload_libraries`; y **probar** los SQL contra un Postgres real (no se ha ejecutado nada).
