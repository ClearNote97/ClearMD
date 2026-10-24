# AGENTS.md — ClearNote_Dev

> **Entrada estándar que los agentes de IA auto-leen.** El **contrato de trabajo** (cómo colaboramos,
> agnóstico de herramienta) vive en **[`README_AGENTS.md`](./README_AGENTS.md)** — léelo **primero**.
> Este archivo suma solo lo **específico de este proyecto**.

## Qué es este proyecto

Plantilla insignia para **apps full-stack en Python** bajo **Spec-Driven Development (SDD)**.
Ver [`README.md`](./README.md) (qué es / cómo instalar) y [`docs/architecture/`](./docs/architecture/)
(arquitectura + gobernanza de datos).

## Roster de agentes (materialízalo)

Este proyecto declara los agentes que necesita, de forma agnóstica, en **[`spec_agents/`](./spec_agents/)**.
Si vas a trabajar con subagentes, **materialízalos a tu formato nativo** siguiendo el protocolo de
`spec_agents/README.md`: por cada `<id>.yaml`, si ya existe un agente para ese rol en tu harness **pregunta**
(reusar / reemplazar / complementar) antes de crearlo; mapea `tools_allowed` y `model_hint` a lo tuyo. Nunca pises en silencio.

## Reglas específicas al trabajar aquí

- **SDD manda:** nada se construye sin spec. El flujo es **Constitución → Spec → Plan → Tareas → Implementación**.
  `spec/` es **prescriptivo** (lo que DEBE ser verdad); `docs/` es **descriptivo** (cómo y por qué quedó así).
- **Gobernanza de datos:** lee `docs/architecture/gobernanza-db.md` + `multi-tenancy.md` **antes** de tocar la DB.
  Las políticas RLS por tabla **nacen en su migración**, no en un archivo suelto.
- ⭐ **Regla de dos aprobadores:** cualquier cambio que **desactive o altere RLS o auditoría** exige **2 revisores humanos**.
- **Convenciones de arranque de datos:** al crear una tabla de estado/referencia, preguntar *"¿va bitemporal?"*;
  modelar la **identidad de los actores** (surrogate `person_id` + documentos versionados) para permitir anonimización.

## Cómo correr (nada se ejecuta por defecto)

- **Entorno:** *Reopen in Container* (VS Code + Dev Containers). `postCreateCommand` prepara `.venv` con **`uv`**.
- **Arranque en un comando (dev):** `./init.sh` → build+up+wait → gobernanza → deps `uv` → migraciones. Idempotente.
- **Gobernanza en prod/CI:** `APP_ENV=prod ./src/database/admin/run-admin.sh` (un solo interruptor `APP_ENV` decide dev/prod; secreto por archivo).
- **Migraciones:** Alembic (`alembic.ini`, `src/database/migrations/`).
- **Ejecución dentro del contenedor** vía `docker exec` (ver contrato §4).

## Stack

Python 3.14 + `uv` · **Polars** (DataFrames) · PostgreSQL 18 + SQLModel / SQLAlchemy 2 / Alembic · Docker Compose.
