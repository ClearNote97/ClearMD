# src/clearmd — The `clearmd` package

Laid out like the ClearNote_Dev template, inside the package (ADR-0014). Dependencies point from `frontend/`
to `backend/api`, and inside the backend toward `use_cases/` and `schemas/` (ADR-0001).

| Folder | Role |
|---|---|
| `backend/` | Application logic: facade, use cases, schemas and services. |
| `frontend/` | Interfaces: CLI, presenter and, in their phase, the GUIs. |
| `i18n/` | EN/ES message catalogs shared by both sides (feature 001, ADR-0012). |
