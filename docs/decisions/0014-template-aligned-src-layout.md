# ADR-0014: `src/` layout aligned with the ClearNote_Dev template

- **Status:** accepted
- **Date:** 2026-10-25
- **Supersedes:** the module names of ADR-0001 (`clearmd.core`, `clearmd.converters`, `clearmd.presenter`,
  `clearmd.cli`) and the "docstring instead of a README per folder" rule of ADR-0007.

## Context

The author's templates share one `src/` structure: `backend/` (`api` → `use_cases` → `services`, plus
`schemas`) and `frontend/` (`app`, `views`, `components`, `layout`, `state`, `services`, `visuals`), with a
`README.md` in every folder (principle 8 of the constitution, `README_AGENTS.md` §6). ClearMD had replaced it
with hexagonal names of its own, which made the repo look unlike every other project born from the template,
and left principle 8 without an exception or an application.

Two constraints prevent copying the template literally:

- ClearMD is an installable package (ADR-0007). Top-level packages named `backend` and `frontend` would
  clash with any other distribution that uses those names.
- The template's `api/` is an HTTP layer. ClearMD has no server: its interfaces call the backend in-process.

## Decision

The template folders live **inside** the `clearmd` package:

```
src/clearmd/
  backend/
    api/        the facade every interface calls (plan_batch, run_batch) + the composition root
    schemas/    immutable data that crosses the facade: plans, reports, events, settings, error codes
    use_cases/  the script: scan → plan → schedule → execute; pure rules; the ports (ports.py)
    services/   implementations of the ports: conversion, detection, worker, settings store, summary
  frontend/
    cli/        the command-line interface
    presenter/  interaction logic shared by the GUIs (MVP, feature 005)
    <gui>/      ttk, qt, flet in their phase, each with the template's app/ views/ components/ layout/
  i18n/         the EN/ES message catalogs, shared by backend and frontend (ADR-0012)
```

The hexagonal architecture of ADR-0001 is kept, expressed with the template's names, following Clean
Architecture: the **ports belong to the use cases** that need them, and `services/` implements them.

**Dependency rule** (enforced by an architecture test):

| Package | May import |
|---|---|
| `backend.schemas`, `backend.use_cases`, `i18n` | standard library only (plus `schemas` from `use_cases`) |
| `backend.services` | `schemas`, `use_cases`, `i18n` and third-party libraries |
| `backend.api` | everything in `backend` and `i18n` (it wires the adapters) |
| `frontend.*` | `backend.api`, `backend.schemas` and `i18n` — never `use_cases` or `services` |

**One `README.md` per folder**, as in the template. They are excluded from the wheel through
`[tool.uv.build-backend] wheel-exclude`, which was the only reason ADR-0007 had dropped them.

The roster in `spec_agents/` is adapted to ClearMD as part of the same alignment: it is the project's roster,
not untouched doctrine, so ADR-0011's list of verbatim template files no longer includes it.

## Consequences

- **Gains:** the repo reads like every other ClearNote_Dev project; principle 8 applies as written (backend
  and frontend layers) instead of needing an exception; the dependency rule is stated per folder and tested.
- **Costs:** an extra nesting level (`clearmd.backend.use_cases.planning`); the template's HTTP wording for
  `api/` has to be reinterpreted as an in-process facade, explained in its README.

## Alternatives considered

- **Literal template (`src/backend`, `src/frontend` as top-level packages):** rejected; name clashes in an
  installable package and in a PyInstaller bundle.
- **Keep the hexagonal names (`core`, `converters`):** rejected; it breaks the consistency of the author's
  templates, which is the point of having them.
