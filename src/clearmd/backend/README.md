# src/clearmd/backend — Application logic

What the template calls the server. ClearMD has no HTTP: interfaces call `api/` in the same process.

| Folder | Role |
|---|---|
| `api/` | Facade (`plan_batch`, `run_batch`) and composition root. The only door for `frontend/`. |
| `schemas/` | Immutable data that crosses the facade: plans, reports, events, settings, error codes. |
| `use_cases/` | The script of a batch (scan → plan → schedule → execute), pure rules and the ports. |
| `services/` | Implementations of the ports: markitdown and own converters, detection, worker process. |

`schemas/` and `use_cases/` import only the standard library; an architecture test enforces it (ADR-0014).
