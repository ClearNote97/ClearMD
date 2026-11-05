# docs/architecture — System design (as built, features 001–006)

ClearMD follows a **ports and adapters** architecture (ADR-0001), laid out with the ClearNote_Dev template's
`backend/` and `frontend/` folders inside the package (ADR-0014). The use cases know neither the interfaces nor
the conversion libraries; heavy and untrusted work runs in a separate worker process (ADR-0015).

```
  frontend/                          backend/
 ┌──────────────────────────┐       ┌──────────────────────────────────────────────────────────┐
 │ cli    ttk ─► presenter  │       │ api/        plan_batch · run_batch · load_settings        │
 │ (qt, flet: 007–008, on   │ ───►  │             composition.py builds every service           │
 │  the same presenter)     │       │   │                                                       │
 └──────────────────────────┘       │   ▼                                                       │
     only api + schemas + i18n      │ use_cases/  scan → plan → order → execute → report        │
                                    │   ▲  ports.py · stdlib only     schemas/ (data, stdlib)   │
                                    │   │ implement                                             │
                                    │ services/   detection · summary · settings_store · worker ┤
                                    └───────────────────────────────────────────────────────┼───┘
                                                                                            │ pipe
                                                       ┌────────────────────────────────────▼──┐
                                                       │ worker: markitdown, magika, tex, odt  │
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
| | `conversion/markdown_out/` | The output guarantee shared by ClearMD's own converters (ADR-0023, ADR-0024): escaped copies, marked block lines, the final `neutralize` pass, joining rules, link targets. |
| | `conversion/xmltree` | The XML reader for untrusted XML, standard library only (shared by `.odt` and the article mode): a pyexpat tree, DOCTYPE and entities refused, limits on elements, depth and characters, only the encodings OpenDocument uses, the block mark stripped. |
| | `conversion/html/` | The HTML article mode (feature 004, ADR-0025): trafilatura finds the article (given the page's bytes, never a URL; imported only in the worker), the limited XML reader reads it again, `render` + `writer/` write it (standard library only, with its own architecture rule); no article means the whole page through markitdown, with a note. |
| | `conversion/inline` | Inline text as ClearMD's own converters write it (`.odt`, the article mode), standard library only: runs with their properties, emphasis Markdown can hold (an exact check of CommonMark's emphasis algorithm), links by the rules of ADR-0023, the growth budget for repeated addresses. |
| | `conversion/odt/` | ClearMD's own OpenDocument converter (feature 003, ADR-0024), standard library only: `package` (type, encryption, parts under size caps), `styles` (with parents), `render` + `writer/` + `tables` (the subset, the growth budget), `mathml/` (MathML → LaTeX, StarMath fallback). |
| | `conversion/tex/` | ClearMD's own LaTeX converter (feature 002, ADR-0006/0022): `source` (real encoding), `parsing/` (pylatexenc specs, the walker, the mask), `includes` (inside the folder only), `macros/` (budgeted expansion), `render` + `writer/` + `tables` (the subset, written through `markdown_out`), `nodes` (iterative walks), `images` (links from the output file), `document` (includes spliced in place, then one render). |
| | `detection/` | Extension (CLI process), magika by content (worker), only for files without an extension. |
| | `summary/` | `Resumen_ClearMD.md`: name table, sections (including “Converted with notes”), history, escaping of untrusted names. |
| | `rejections` | How a rejection is told (UX contract §3): its kind, the precise reason with the file's value and the limit, and what to do; one wording for the CLI, the summary and the GUIs (exported by the facade). |
| | `settings_store`, `clock` | `settings.toml` on each OS (platformdirs); the system clock. |
| `frontend` | `cli/app.py` | Arguments, settings and language, prompt, dry run, progress, Ctrl+C, summary, `--open`, exit codes. |
| | `presenter/` | Every GUI's interaction logic (feature 005, ADR-0026), standard library only: the seven states and what each enables, the intents, the work on a worker thread brought back to the UI thread, every text from the catalogs, the four steps and each row's file icon; tested with a fake view. |
| | `ttk/` | The ttkbootstrap window (ADR-0026, ADR-0027): it draws what the presenter gives it — the rail with the steps, one page per step, the dialogs — in ClearMD's look (`brand`: two themes, rounded image elements; `art`: Pillow drawings). |
| | `assets/` | The logo, the app icon, the splash and the file icons (ADR-0027), generated by `tests/gui/make_assets.py`, shared by every GUI. |
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
