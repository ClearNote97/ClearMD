# src/database — Persistencia y gobernanza

Todo lo relativo a la base de datos.

| Carpeta | Rol |
|---|---|
| `admin/` | **Gobernanza**: roles, schemas, grants, RLS, audit, mantenimiento (SQL idempotente). |
| `app/` | Modelos (SQLModel) y repositorios del schema transaccional `app`. |
| `analytics/` | Queries y datasets del lado analítico (`gold`). |
| `migrations/` | Entorno **Alembic**; las migraciones generadas van a `versions/`. |

> **`connection.py`** es la **fuente única** de la resolución de conexión (gira sobre `APP_ENV`, secreto por
> archivo, dev/prod). Lo consumen `session.py` (engine + `get_session`) y `migrations/env.py` (Alembic), para que
> app y migraciones nunca diverjan. Los scripts `admin/run-admin.sh` e `init.sh` replican la misma lógica en bash.
