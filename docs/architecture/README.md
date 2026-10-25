# docs/architecture — System design (as built, features 001–002)

ClearMD follows a **ports and adapters** architecture (ADR-0001), laid out with the ClearNote_Dev template's
`backend/` and `frontend/` folders inside the package (ADR-0014). The use cases know neither the interfaces nor
the conversion libraries; heavy and untrusted work runs in a separate worker process (ADR-0015).

```
  frontend/                          backend/
 ┌──────────────────────────┐       ┌──────────────────────────────────────────────────────────┐
 │ cli  (ttk, qt, flet      │       │ api/        plan_batch · run_batch · load_settings        │
 │       in their phase)    │ ───►  │             composition.py builds every service           │
 │    presenter (005)       │       │   │                                                       │
 └──────────────────────────┘       │   ▼                                                       │
     only api + schemas + i18n      │ use_cases/  scan → plan → order → execute → report        │
                                    │   ▲  ports.py · stdlib only     schemas/ (data, stdlib)   │
                                    │   │ implement                                             │
                                    │ services/   detection · summary · settings_store · worker ┤
                                    └───────────────────────────────────────────────────────┼───┘
                                                                                            │ pipe
                                                       ┌────────────────────────────────────▼──┐
                                                       │ worker: markitdown + magika + .tex    │
                                                       │ convert and detect, one file at a time │
                                                       └────────────────────────────────────────┘
```

**Dependency rule** (enforced by `tests/unit/test_architecture.py`): `backend/schemas`, `backend/use_cases`
and `i18n` import only the standard library; `backend/services` implements the ports and is the only place with
third-party imports; `frontend/` talks only to `backend/api`, `backend/schemas` and `i18n`. The CLI process
never imports markitdown, magika or pylatexenc: only the worker does (001 AC-19 and 002 AC-03, each tested in
a fresh process).

## Modules

| Package | Module | Role |
|---|---|---|
| `schemas` | `formats` | `FormatId`, the extension table, ZIP-based formats, the fixed names (`ClearMD_Output`, `OutputMD`, `Resumen_ClearMD.md`). |
| | `limits` | `Limits` and the speeds and memory factors per format measured in benchmarks [001](../benchmarks/001-conversion-limits.md) and [002](../benchmarks/002-tex-converter.md). |
| | `errors` | `ErrorCode`, `SkipReason` (each with its catalog keys), `ConversionError`, `Cancelled`. |
| | `notes` | `ConversionNote` (a `NoteKind` and its `NoteItem`s with a `NoteReason`): language-neutral data that the catalogs put into words (ADR-0022). |
| | `models` | Frozen `ConversionResult` (Markdown + notes), `BatchPlan`, `PlannedConversion`, `SkippedItem`, `PlanWarning`, `ConversionOutcome`, `BatchReport`, `OutputRootReport`. |
| | `events` | `ScanProgress`, `PlanReady`, `ConversionStarted` (with the time left), `ConversionFinished`, `BatchFinished`. |
| | `settings` | `Settings` and its allowed values (ADR-0012, ADR-0017). |
| `use_cases` | `ports` | `FormatDetector`, `ConversionRunner`, `Clock`. |
| | `scanning` | Walks the inputs; never follows symlinks, never enters `ClearMD_Output`; skips hidden, lock, `.md`, `.zip`, oversized files. |
| | `archive` | Reads a ZIP's central directory only: uncompressed size, whole-file ratio, size of the text parts. |
| | `paths` | Output parent (root/home rule), targets, collision-free names. |
| | `planning` | Detection, archive check, memory skip, names, cost order, slow-file warnings → `BatchPlan`. |
| | `scheduling`, `estimation` | Cheapest first; time left corrected with the measured speed. |
| | `execution` | Warm-up, one file at a time, atomic UTF-8/LF writes, failure isolation, stopped files, unwritable roots, cancellation. |
| | `reporting`, `settings`, `cancel` | One report per output root; settings parse/serialize; the cancel token. |
| `services` | `worker/` | `WorkerRunner` (supervisor: `Ready` handshake, time and memory limits with psutil, cancellation, replacement) and the child process. |
| | `conversion/` | The registry (`convert(source, detection, target)`), the markitdown adapter (exception mapping verified on fixtures), `safe_files` (no links, size cap). |
| | `conversion/tex/` | ClearMD's own LaTeX converter (feature 002, ADR-0006/0022): `source` (real encoding), `context` (pylatexenc specs), `includes` (inside the folder only), `macros` (budgeted expansion), `render` + `tables` (the subset and the output guarantee of ADR-0023: escaped copies, marked block lines, a final `neutralize` pass), `nodes` (iterative walks), `images` (links from the output file), `document` (includes spliced in place, then one render). |
| | `detection/` | Extension (CLI process), magika by content (worker), only for files without an extension. |
| | `summary/` | `Resumen_ClearMD.md`: name table, sections (including “Converted with notes”), history, escaping of untrusted names. |
| | `settings_store`, `clock` | `settings.toml` on each OS (platformdirs); the system clock. |
| `frontend` | `cli/app.py` | Arguments, settings and language, prompt, dry run, progress, Ctrl+C, summary, `--open`, exit codes. |
| `i18n` | | EN/ES catalogs, plain-word durations, stopwatch time, gigabytes per language. |

## Flow of a batch (ADR-0010, ADR-0015, ADR-0016)

1. **Plan** (`plan_batch`, nothing written): scan the inputs; detect each format (extension, or magika in the
   worker for files without one); check ZIP-based documents from their index; skip what would not fit in the
   worker's memory; compute collision-free targets in `ClearMD_Output/OutputMD/`; order by estimated time;
   warn about files that may exceed the time limit.
2. **Decide**: existing outputs are overwritten, kept, or asked about once (CLI flags, settings or prompt).
3. **Execute** (`run_batch`): warm the worker up; convert one file at a time; the supervisor stops a file over
   the time or memory limit and replaces the worker; Markdown is written atomically; Ctrl+C or Cancel stops the
   current file at once.
4. **Report**: one `Resumen_ClearMD.md` per output folder, with the name table, times, problems and history.

## The worker protocol

`ConvertRequest` / `DetectRequest` go down the pipe; `Converted`, `Detected` or `Failed` come back. The worker
sends `Ready` once its converters are loaded: time limits count from the moment a file is sent, never during
start-up. A `None` request asks it to exit.
