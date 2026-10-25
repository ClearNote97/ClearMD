# src/ — Implementation (the `clearmd` package)

`src/` layout with a real package (ADR-0007), organized like the ClearNote_Dev template **inside** the package
(ADR-0014): `backend/` and `frontend/`, with a `README.md` in every folder (excluded from the wheel).

| Folder | Role |
|---|---|
| `clearmd/backend/api/` | Facade every interface calls (`plan_batch`, `run_batch`) + composition root. In-process, no HTTP. |
| `clearmd/backend/schemas/` | Immutable data crossing the facade: plans, reports, events, settings, error codes. |
| `clearmd/backend/use_cases/` | Scan → plan → schedule → execute, pure rules and the ports. Standard library only. |
| `clearmd/backend/services/` | The ports' implementations: markitdown and own converters, detection, worker process. |
| `clearmd/frontend/cli/` | Command-line interface: the first one, and the one acceptance tests drive. |
| `clearmd/frontend/presenter/` | Interaction logic shared by the GUIs (MVP, feature 005). |
| `clearmd/i18n/` | EN/ES message catalogs (feature 001, ADR-0012). |

**Dependency rule** (an architecture test enforces it, ADR-0014): `schemas/` and `use_cases/` import only the
standard library; `services/` implements the ports and is the only place with third-party imports; `frontend/`
talks only to `backend/api`, `backend/schemas` and `i18n`. GUIs (`ttk/`, `qt/`, `flet/`) arrive in
`frontend/` in their phase (see `spec/roadmap.md`).
