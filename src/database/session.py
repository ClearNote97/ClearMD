"""Engine y sesiones de base de datos (SQLModel + SQLAlchemy 2).

Fuente única de la conexión para la aplicación (los endpoints/servicios piden
sesiones aquí). La **resolución de la URL** (APP_ENV, secretos, dev/prod) vive en
`connection.py` — este módulo solo crea el engine y entrega sesiones, para que la
app y Alembic (`migrations/env.py`) compartan exactamente la misma lógica.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlmodel import Session

from .connection import build_database_url

# --- Engine: un único pool de conexiones para todo el proceso ---------------
# `pool_pre_ping` evita usar conexiones muertas (típico tras reinicios del contenedor).
# `echo` se controla por entorno para depurar SQL sin tocar el código.
# La URL la resuelve connection.build_database_url() (gira sobre APP_ENV).
engine = create_engine(
    build_database_url(),
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "").lower() in {"1", "true", "yes"},
)


def get_session() -> Iterator[Session]:
    """Dependencia estilo FastAPI: entrega una sesión y garantiza su cierre.

    Uso:
        @app.get("/items")
        def listar(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session
