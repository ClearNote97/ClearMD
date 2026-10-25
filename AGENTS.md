# AGENTS.md — ClearMD

> **Standard entry point that AI agents read automatically.** The **working contract** (how we collaborate,
> tool-agnostic) lives in **[`README_AGENTS.md`](./README_AGENTS.md)** (in Spanish) — read it **first**.
> This file adds only what is **specific to this project**.

## What this project is

**ClearMD**: a 100% local desktop app that converts documents to Markdown. A backend with pure use cases and
four interfaces (CLI, ttkbootstrap, PySide6, flet), laid out like the template (`src/clearmd/backend/`,
`src/clearmd/frontend/`, ADR-0014), designed for non-technical users first. It was born from the
ClearNote_Dev template and pruned (ADR-0009). See [`README.md`](./README.md),
[`docs/architecture/`](./docs/architecture/) and the decision index in [`docs/decisions/`](./docs/decisions/).

**Kind of work (axis 1):** application development (SDD). **SQL (axis 2):** no (ADR-0002).

## Agent roster (materialize it)

Declared tool-agnostically in **[`spec_agents/`](./spec_agents/)** (8 roles, in Spanish). To materialize it,
follow the protocol in `spec_agents/README.md`: if your harness already has an agent for a role, **ask**
(reuse / replace / complement) before creating one. Never overwrite silently.

## Project-specific rules

- **SDD rules:** nothing is built without a spec. **Constitution → Spec → Plan → Tasks → Implementation**.
  `spec/` is **prescriptive**; `docs/` is **descriptive**. The current feature is in `spec/roadmap.md`.
- **Non-trivial decision = ADR** in `docs/decisions/` (plus a line in its index). An accepted ADR is never
  rewritten to change the decision: a new one supersedes it.
- **Dependency rule** (ADR-0014): `backend/schemas` and `backend/use_cases` import only the standard library;
  third-party imports live only in `backend/services`; `frontend/` talks only to `backend/api`,
  `backend/schemas` and `i18n`. markitdown and magika are imported only inside the worker process (ADR-0015).
- **A `README.md` in every folder** (template standard), excluded from the wheel.
- **No user-facing string literals:** every text comes from the EN/ES catalogs (ADR-0012).
- **100% local:** no code makes network requests (ADR-0005).
- **Input documents are untrusted:** size and archive limits, no symlink following, no ZIP, conversions in a
  worker process with time and memory limits (ADR-0010, ADR-0015).
- **GUIs follow `spec/contracts/ux.md`** (ADR-0013).
- **Only what is used:** each GUI, its graphics libraries and PyInstaller arrive in their roadmap phase.
- **Language:** project text in English; template doctrine stays in Spanish (ADR-0011). Talk to the author in
  their language.

## How to run (nothing runs by default)

- **Environment:** *Reopen in Container* (VS Code + Dev Containers). `postCreateCommand` runs `init.sh`, which
  installs the dependencies with **`uv`** (reproducible `uv.lock`).
- **Run inside the container** through `docker exec` (contract §4). From the host:
  `docker exec -w /workspaces/<folder> <folder>_dev uv run <command>`.
- **Quality gate:** `uv run pytest` · `uv run ruff check . && uv run ruff format --check .` · `uv run mypy`.
- **CLI:** `uv run clearmd --help`.

## Stack

Python 3.12–3.14 supported, 3.14 in development (ADR-0018) + `uv` (`uv_build`, `src/` layout) · markitdown
0.1.9 · platformdirs · psutil · pytest · ruff · mypy. Details and reasons in `spec/constitution/03_stack.md`.
