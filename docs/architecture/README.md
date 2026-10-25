# docs/architecture — System design

ClearMD follows a **ports and adapters** architecture (ADR-0001), laid out with the ClearNote_Dev template's
`backend/` and `frontend/` folders inside the package (ADR-0014). The use cases know neither the interfaces nor
the conversion libraries; heavy and untrusted work runs in a separate worker process (ADR-0015).

```
  frontend/                          backend/
 ┌──────────────────────────┐       ┌──────────────────────────────────────────────────────────┐
 │ cli   ttk   qt   flet    │       │ api/        facade (plan_batch, run_batch) + composition  │
 │        │                 │ ───►  │   │                                                       │
 │    presenter (MVP)       │       │   ▼                                                       │
 └──────────────────────────┘       │ use_cases/  scan → plan → schedule → execute, ports       │
          only api + schemas        │   ▲  (stdlib only)        schemas/ (data, stdlib only)    │
                                    │   │ implement                                             │
                                    │ services/   detection · summary · settings · worker ──┐   │
                                    └───────────────────────────────────────────────────────┼───┘
                                                                                            │ pipe
                                                          ┌─────────────────────────────────▼───┐
                                                          │ worker process: markitdown + magika │
                                                          │ (later .tex, .odt, article mode)    │
                                                          └─────────────────────────────────────┘
```

**Dependency rule** (an architecture test enforces it): `backend/schemas`, `backend/use_cases` and `i18n` import
only the standard library; `backend/services` implements the ports and is the only place with third-party
imports; `frontend/` talks only to `backend/api`, `backend/schemas` and `i18n`. The CLI process never imports
markitdown or magika: only the worker does.

Feature 001's [plan](../../spec/features/001_batch-conversion-backend-cli/plan.md) details every module.

## Flow of a batch conversion (ADR-0010, ADR-0015, ADR-0016)

1. The interface receives files and/or folders, and optionally an output folder.
2. `use_cases` scans the inputs (skipping hidden files, symlinks, oversized files and suspicious archives),
   detects the format of each file (by extension; by content in the worker) and computes the destinations in
   `ClearMD_Output/OutputMD/` (resolving collisions) → **batch plan**, ordered from the cheapest to the most
   expensive file.
3. The interface shows the plan; if there are existing outputs, the user decides.
4. `use_cases` executes: the worker converts one file at a time; the supervisor enforces the time and memory
   limits and cancels at once when asked. The Markdown is written atomically. A failure does not stop the
   batch.
5. `Resumen_ClearMD.md` is written in each output root: the name table, skips, failures and the history.

> This document describes the target design. It is updated to the as-built design when feature 001 closes.
