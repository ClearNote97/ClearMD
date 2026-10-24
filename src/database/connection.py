"""Resolución de conexión y SECRETOS — FUENTE ÚNICA DE VERDAD.

TODO gira sobre **APP_ENV**: `dev` (por defecto) o `prod`. Lo único que cambia
entre entornos es **dónde vive cada secreto**; el resto se deriva.

Lo consumen:
  - `session.py`            → engine + sesiones de la app.
  - `migrations/env.py`     → Alembic (autogenerate y upgrade).
  - (variante bash equivalente) `admin/run-admin.sh` e `init.sh`.

Reglas (idénticas en Python y en los scripts bash):
  1. Los secretos se leen SIEMPRE de un ARCHIVO (nunca en claro en el repo).
     Cada secreto `X` se resuelve por convención, derivada de APP_ENV:
       dev  → ./secrets/<archivo>            (repo, gitignored)
       prod → /run/secrets/<nombre>          (lo monta el orquestador/vault)
     La env var `<X>_FILE` sobreescribe la ruta en cualquier entorno.
  2. Para la DB: si `DATABASE_URL` viene completa y SIN placeholder, se respeta.
  3. La URL se arma con `URL.create()` (escapa credenciales; nada de f-strings).
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import URL

# Raíz del proyecto: connection.py está en src/database/ → subir 2 niveles.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Driver sincrónico por defecto (psycopg2, ver requirements.txt).
_DRIVER = "postgresql+psycopg2"


def _canon_env(value: str | None) -> str:
    """Normaliza APP_ENV: 'prod'/'production' → 'prod'; cualquier otra cosa → 'dev'."""
    return "prod" if (value or "").strip().lower().startswith("prod") else "dev"


# Valor canónico del entorno, calculado una vez al importar.
APP_ENV: str = _canon_env(os.getenv("APP_ENV"))


def is_prod() -> bool:
    """True si estamos en producción (según APP_ENV)."""
    return APP_ENV == "prod"


# --- Secretos genéricos (reutilizable para DB, SECRET_KEY, API keys, etc.) ----
def secret_path(env_file_var: str, *, dev_filename: str, prod_name: str) -> str:
    """Ruta de un secreto, derivada de APP_ENV (o el override `<X>_FILE`).

    - `env_file_var`: nombre de la env var que puede forzar la ruta (p. ej. 'DB_PASSWORD_FILE').
    - `dev_filename` : archivo dentro de ./secrets/ en desarrollo (p. ej. 'db_password.txt').
    - `prod_name`    : nombre del secreto en /run/secrets/ en producción (p. ej. 'db_password').
    """
    override = os.getenv(env_file_var)
    if override:
        return override
    if is_prod():
        return f"/run/secrets/{prod_name}"
    return str(PROJECT_ROOT / "secrets" / dev_filename)


def read_secret(
    env_file_var: str,
    *,
    dev_filename: str,
    prod_name: str,
    plain_var: str | None = None,
) -> str | None:
    """Lee el contenido de un secreto por archivo (o de `plain_var` en claro, desaconsejado).

    Devuelve `None` si no existe el archivo ni la variable en claro (secreto opcional).
    """
    path = secret_path(env_file_var, dev_filename=dev_filename, prod_name=prod_name)
    if path and Path(path).is_file():
        return Path(path).read_text(encoding="utf-8").strip()
    return os.getenv(plain_var) if plain_var else None


# --- Accesos con nombre para los secretos del proyecto ------------------------
def db_password() -> str | None:
    """Contraseña de la base de datos."""
    return read_secret(
        "DB_PASSWORD_FILE", dev_filename="db_password.txt", prod_name="db_password",
        plain_var="DB_PASSWORD",  # último recurso: no recomendado
    )


def app_secret_key() -> str | None:
    """Clave secreta de la aplicación (firmas de sesión/tokens)."""
    return read_secret(
        "SECRET_KEY_FILE", dev_filename="app_secret_key.txt", prod_name="app_secret_key",
    )


def ai_api_key() -> str | None:
    """API key del proveedor de IA (opcional; None si no está configurada)."""
    return read_secret(
        "AI_API_KEY_FILE", dev_filename="ai_api_key.txt", prod_name="ai_api_key",
    )


# --- URL de conexión a la base de datos --------------------------------------
def build_database_url() -> URL | str:
    """Devuelve la URL de conexión según APP_ENV y su secreto correspondiente."""
    # 1. URL completa y usable provista por el entorno → se respeta.
    explicit = os.getenv("DATABASE_URL")
    if explicit and "PASSWORD_HERE" not in explicit:
        return explicit

    # 2. Construcción desde piezas + secreto.
    missing = [v for v in ("DB_HOST", "DB_NAME", "DB_USER") if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Configuración de DB incompleta (falta: {', '.join(missing)}). "
            "Define DATABASE_URL, o DB_HOST/DB_NAME/DB_USER + el secreto de la "
            f"contraseña. APP_ENV={APP_ENV}."
        )

    return URL.create(
        _DRIVER,
        username=os.getenv("DB_USER"),
        password=db_password(),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )


def database_url_string() -> str:
    """Como `build_database_url()` pero siempre `str` con la contraseña (para Alembic)."""
    url = build_database_url()
    return url.render_as_string(hide_password=False) if isinstance(url, URL) else url
