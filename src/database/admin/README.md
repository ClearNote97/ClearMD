# src/database/admin — Gobernanza de datos (SQL de bootstrap)

SQL **idempotente** que establece la gobernanza, en orden numérico (`00_`…`06_`), corrido por
`run-admin.sh`. Diseño completo en `docs/architecture/gobernanza-db.md`; manifiesto en
`admin-manifest.yaml`.

| Archivo | Qué hace |
|---|---|
| `00_create_extensions.sql` | Extensiones (pgcrypto, pgaudit, pg_cron…). |
| `01_create_roles.sql` | Roles least-privilege (sin passwords). |
| `02_create_schemas.sql` | Schemas (app, admin, gold; bronze/silver comentados). |
| `03_grants.sql` | Permisos + `ALTER DEFAULT PRIVILEGES`. |
| `04_rls_policies.sql` | Row-Level Security (tenant / subárbol). |
| `05_audit_triggers.sql` | Trío de auditoría (audit_log, job_run/step, governance_registry). |
| `06_maintenance.sql` | Mantenimiento (pg_partman, pg_cron, ANALYZE). |

> ⭐ Cambios a RLS o audit requieren **dos aprobadores**.
>
> **Cómo se aplica:** en dev, `./init.sh` (raíz) lo canaliza al contenedor `db`. En prod/CI,
> `APP_ENV=prod ./run-admin.sh` (un solo interruptor `APP_ENV` decide dónde vive el secreto; ver `../connection.py`).
