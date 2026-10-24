# AGENTS.md — ClearMD

> **Entrada estándar que los agentes de IA auto-leen.** El **contrato de trabajo** (cómo colaboramos,
> agnóstico de herramienta) vive en **[`README_AGENTS.md`](./README_AGENTS.md)** — léelo **primero**.
> Este archivo suma solo lo **específico de este proyecto**.

## Qué es este proyecto

**ClearMD**: app de escritorio 100% local que convierte documentos a Markdown. Un núcleo puro con cuatro
adaptadores de interfaz (CLI, ttkbootstrap, PySide6, flet). Nació de la plantilla ClearNote_Dev y se podó
(ADR-0009). Ver [`README.md`](./README.md), [`docs/architecture/`](./docs/architecture/) y el índice de
decisiones en [`docs/decisions/`](./docs/decisions/).

**Tipo de trabajo (Eje 1):** desarrollo de aplicaciones (SDD). **SQL (Eje 2):** no (ADR-0002).

## Roster de agentes (materialízalo)

Declarado de forma agnóstica en **[`spec_agents/`](./spec_agents/)** (8 roles). Para materializarlo sigue el
protocolo de `spec_agents/README.md`: si ya existe un agente para ese rol en tu harness, **pregunta**
(reusar / reemplazar / complementar) antes de crearlo. Nunca pises en silencio.

## Reglas específicas al trabajar aquí

- **SDD manda:** nada se construye sin spec. **Constitución → Spec → Plan → Tareas → Implementación**.
  `spec/` es **prescriptivo**; `docs/` es **descriptivo**.
- **Decisión no trivial = ADR** en `docs/decisions/` (y una línea en su índice). Un ADR aceptado no se reescribe:
  se reemplaza con uno nuevo.
- **El núcleo no importa nada de afuera** (`clearmd.core` sin GUIs ni librerías de conversión). Solo
  `clearmd.converters` importa markitdown (ADR-0001, ADR-0004).
- **100% local:** ningún código hace peticiones de red (ADR-0005).
- **Los documentos de entrada no son confiables:** límites de tamaño, sin seguir symlinks, cuidado con zips
  (ADR-0010).
- **Solo lo que se usa:** cada GUI, su librería gráfica y PyInstaller entran en su fase del roadmap, no antes.

## Cómo correr (nada se ejecuta por defecto)

- **Entorno:** *Reopen in Container* (VS Code + Dev Containers). `postCreateCommand` corre `init.sh`, que
  instala las dependencias con **`uv`** (`uv.lock` reproducible).
- **Ejecución dentro del contenedor** vía `docker exec` (contrato §4). Desde el host:
  `docker exec -w /workspaces/<carpeta> <carpeta>_dev uv run <comando>`.
- **Calidad (el gate):** `uv run pytest` · `uv run ruff check . && uv run ruff format --check .` · `uv run mypy`.
- **CLI:** `uv run clearmd --help`.

## Stack

Python 3.14 + `uv` (`uv_build`, layout `src/`) · markitdown 0.1.9 · pylatexenc · trafilatura · platformdirs ·
pytest · ruff · mypy. Detalle y porqués en `spec/constitution/03_stack.md`.
