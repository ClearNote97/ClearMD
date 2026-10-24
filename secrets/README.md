# secrets/ — Secretos de desarrollo (NO versionados)

Archivos de secreto para **desarrollo local**, montados como *Docker secrets* (`*_FILE`).
Su **contenido está en `.gitignore`**: nunca se commitea. En producción, los secretos se inyectan
por el orquestador, no desde aquí.

- `db_password.txt` — contraseña de la DB (dev).
- `app_secret_key.txt` — clave de la app (dev).
- `ai_api_key.txt` — API key de IA (dev, opcional).

## Convención (gira sobre `APP_ENV`)

Cada secreto se resuelve en un solo lugar (`src/database/connection.py`, helper `secret_path`), derivado de `APP_ENV`:

| Secreto | dev (`./secrets/…`) | prod (`/run/secrets/…`) | Override |
|---|---|---|---|
| DB | `db_password.txt` | `db_password` | `DB_PASSWORD_FILE` |
| App | `app_secret_key.txt` | `app_secret_key` | `SECRET_KEY_FILE` |
| IA | `ai_api_key.txt` | `ai_api_key` | `AI_API_KEY_FILE` |

> Regla del contrato: cero credenciales en el repo. Placeholders en `.env.example`, valores reales fuera de git.
> En **prod** estos archivos los monta el orquestador/vault en `/run/secrets/`; aquí solo viven los de **dev**.
