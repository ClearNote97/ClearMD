# src/database/migrations — Entorno Alembic

Configuración de migraciones. `env.py` resuelve la conexión vía **`../connection.py`** (la MISMA que la app;
gira sobre `APP_ENV` y el secreto por archivo), usa `SQLModel.metadata` y `version_table_schema='app'`.
Las migraciones **generadas** viven en `versions/`.
Generar: `alembic revision --autogenerate -m "..."`; aplicar: `alembic upgrade head` (dentro del contenedor).
