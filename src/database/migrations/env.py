"""Entorno de migraciones de Alembic.

- La URL de conexión la resuelve `src/database/connection.py` (FUENTE ÚNICA: gira
  sobre `APP_ENV`, lee el secreto del archivo, dev/prod) — la MISMA que usa la app
  en `session.py`. Así Alembic y la app nunca divergen.
- Las migraciones corren como el **dueño** de las tablas (p. ej. `app_owner`); el
  historial de Alembic vive en el schema `app`, no en `public`.
- `target_metadata = SQLModel.metadata` para que `--autogenerate` vea los modelos.
- Frontera: `admin/` es bootstrap (lo corre `run-admin.sh` / `init.sh`); aquí vive la
  **evolución de tablas**, incluidas las **políticas RLS por tabla** (nacen con su tabla).
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# Raíz del proyecto en el path para importar el módulo canónico de conexión.
# env.py está en src/database/migrations/ → subir 3 niveles hasta la raíz.
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.database.connection import build_database_url, database_url_string  # noqa: E402

# Importa aquí tus modelos para que autogenerate los detecte, por ejemplo:
# from src.database.app.models import *  # noqa: F401,F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

# El historial de migraciones vive en el schema `app` (no en `public`, que revocamos).
VERSION_TABLE_SCHEMA = "app"


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse (modo --sql)."""
    context.configure(
        url=database_url_string(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=VERSION_TABLE_SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica las migraciones conectándose a la base (engine desde connection.py)."""
    connectable = create_engine(build_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=VERSION_TABLE_SCHEMA,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
