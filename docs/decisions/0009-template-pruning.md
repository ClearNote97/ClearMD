# ADR-0009: Pruning of the ClearNote_Dev template

- **Status:** accepted
- **Date:** 2026-10-24

## Context

ClearMD was born from the **ClearNote_Dev** template, designed for full-stack apps with PostgreSQL, analytics and web.
The repo's first commit is the untouched template, so that the history shows the starting point. Before
building the development container, **only what the project uses** had to remain: what is not used still has to be
read, maintained and installed.

## Decision

Removed:

| What | Why |
|---|---|
| `alembic.ini`, `src/database/`, `infra/db/`, `secrets/`, `db` service in the compose file, `DB_*` and `COMPOSE_PROFILES` variables, port 5432, `postgresql-client` | No database (ADR-0002) |
| `docs/architecture/gobernanza-db.md`, `multi-tenancy.md`, `docs/data-dictionary/`, `docs/audit/` | They document the database that does not exist |
| `src/analytics/`, `notebooks/`, `data/`, `src/utils/` (Polars helpers), Jupyter extensions | ClearMD does no analytics |
| `src/backend/`, `src/frontend/`, `scripts/nginx/` and the commented-out services (TimescaleDB, Prefect, MLflow, Reflex, Flet web, Nginx) | Web scaffolding; replaced by core + adapters (ADR-0001) |
| `requirements.txt` and the `uv init --no-package` flow | Real package with `pyproject.toml` (ADR-0007) |
| `build-essential` from the `Dockerfile` | Verified: every dependency publishes wheels for Python 3.14; nothing is compiled |
| `docs/business/` | No content; the product context lives in `spec/constitution/` |
| 12 of the 20 roles in `spec_agents/` | Data, analytics, research and database families |

Kept unchanged: `README_AGENTS.md` (a contract copied verbatim between repos), `LICENSE` (MIT),
`.gitattributes`, `.dockerignore`, `spec/constitution/01_principles.md` (template doctrine; the
exceptions are in ADR-0001 and ADR-0002) and `spec/features/000_example/` (format reference until
feature 001 exists).

## Consequences

Measured on 2026-10-24:

| | Before | After |
|---|---|---|
| Docker images | 1,380 MB (app-dev 755 MB + db 625 MB) | **413 MB** (app-dev only) |
| Services in the compose file | 2 active + 6 commented out | 1 |
| Declared Python dependencies | 16 active + 18 commented out (`requirements.txt`) | 4 runtime + 3 development (61 packages resolved in `uv.lock`) |

- **Gains:** an environment anyone understands on opening the repo; a smaller attack surface; faster
  startup.
- **Costs:** the repo drifts away from the template; future ClearNote_Dev improvements will have to be brought over by
  hand and selectively.
