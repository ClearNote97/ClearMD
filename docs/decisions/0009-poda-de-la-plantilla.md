# ADR-0009: Poda de la plantilla ClearNote_Dev

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

ClearMD nació de la plantilla **ClearNote_Dev**, pensada para apps full-stack con PostgreSQL, analítica y web.
El primer commit del repo es la plantilla intacta, para que el historial muestre el punto de partida. Antes de
construir el contenedor de desarrollo debía quedar **solo lo que el proyecto usa**: lo que no se usa también se
lee, se mantiene y se instala.

## Decisión

Se eliminó:

| Qué | Por qué |
|---|---|
| `alembic.ini`, `src/database/`, `infra/db/`, `secrets/`, servicio `db` del compose, variables `DB_*` y `COMPOSE_PROFILES`, puerto 5432, `postgresql-client` | Sin base de datos (ADR-0002) |
| `docs/architecture/gobernanza-db.md`, `multi-tenancy.md`, `docs/data-dictionary/`, `docs/audit/` | Documentan la base de datos que no existe |
| `src/analytics/`, `notebooks/`, `data/`, `src/utils/` (helpers de Polars), extensiones de Jupyter | ClearMD no hace analítica |
| `src/backend/`, `src/frontend/`, `scripts/nginx/` y los servicios comentados (TimescaleDB, Prefect, MLflow, Reflex, Flet web, Nginx) | Andamiaje web; se reemplaza por núcleo + adaptadores (ADR-0001) |
| `requirements.txt` y el flujo `uv init --no-package` | Paquete real con `pyproject.toml` (ADR-0007) |
| `build-essential` del `Dockerfile` | Verificado: todas las dependencias publican wheels para Python 3.14; nada se compila |
| `docs/business/` | Sin contenido; el contexto del producto vive en `spec/constitution/` |
| 12 de los 20 roles de `spec_agents/` | Familias de datos, analítica, investigación y base de datos |

Se conservó sin cambios: `README_AGENTS.md` (contrato que se copia idéntico entre repos), `LICENSE` (MIT),
`.gitattributes`, `.dockerignore`, `spec/constitution/01_principles.md` (doctrina de la plantilla; las
excepciones están en ADR-0001 y ADR-0002) y `spec/features/000_example/` (referencia de formato hasta que
exista la feature 001).

## Consecuencias

Medido el 2026-10-24:

| | Antes | Después |
|---|---|---|
| Imágenes Docker | 1.380 MB (app-dev 755 MB + db 625 MB) | **413 MB** (solo app-dev) |
| Servicios en el compose | 2 activos + 6 comentados | 1 |
| Dependencias Python declaradas | 16 activas + 18 comentadas (`requirements.txt`) | 4 de ejecución + 3 de desarrollo (61 paquetes resueltos en `uv.lock`) |

- **Se gana:** un entorno que cualquiera entiende al abrir el repo; menos superficie de ataque; arranque más
  rápido.
- **Se paga:** el repo se aleja de la plantilla; las mejoras futuras de ClearNote_Dev habrá que traerlas a
  mano y de forma selectiva.
