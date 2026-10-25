# Plan — Feature 001: batch conversion, backend + CLI

> The **how**. It must be executable without guessing. Criteria: [`spec.md`](./spec.md).

## Architecture

Template layout inside the package (ADR-0014). Every folder carries its `README.md`.

```
src/clearmd/
  backend/
    schemas/                  # stdlib only
      formats.py              # FormatId, extension table, ZIP-based formats, skip-only extensions, names
      limits.py               # Limits dataclass (size, archive, time, memory) + cost weights per format
      errors.py               # ErrorCode, SkipReason (each maps to a catalog key)
      models.py               # frozen: Detection, PlannedConversion, SkippedItem, BatchPlan,
                              #   ConversionOutcome, BatchReport, OutputRootReport
      events.py               # ScanProgress, PlanReady, ConversionStarted, ConversionFinished, BatchFinished
      settings.py             # Settings dataclass + defaults
    use_cases/                # stdlib (+ schemas) only
      ports.py                # Protocols: FormatDetector, ConversionRunner, SummaryWriter, Clock
      cancel.py               # CancelToken (wraps threading.Event)
      paths.py                # pure: output_parent_for(), output_root_for(), target_for(), resolve_names()
      archive.py              # inspect_archive(): uncompressed size + ratio from the ZIP central directory
      scanning.py             # expand inputs into candidates + skipped items
      planning.py             # build_plan()
      scheduling.py           # order_by_cost()
      execution.py            # execute_plan(), atomic_write()
      settings.py             # parse_settings() / serialize_settings() (pure)
    services/                 # the only place with third-party imports
      detection/
        extension.py          # ExtensionDetector (stdlib, runs in the CLI process)
        chain.py              # ChainDetector: first non-None wins
      conversion/
        markitdown_adapter.py # MarkItDownConverter + exception mapping (imported only by the worker)
        registry.py           # FormatId -> converter, built inside the worker
      worker/
        protocol.py           # request/response tuples sent through the pipe
        child.py              # worker_main(): loads registry + magika once, serves detect/convert
        supervisor.py         # WorkerRunner: implements ConversionRunner and the content FormatDetector;
                              #   enforces time, memory (psutil) and cancellation; replaces the worker
      summary/
        writer.py             # MarkdownSummaryWriter: renders Resumen_ClearMD.md, merges the history
      settings_store.py       # settings path (platformdirs), load_settings()
    api/
      composition.py          # the only place that builds services
      __init__.py             # plan_batch(), run_batch() — what every interface calls
  i18n/
    __init__.py               # Catalog, load_catalog(), resolve_language()
    en.toml, es.toml
  frontend/
    cli/app.py                # argparse, prompts, progress rendering, exit codes
```

**Dependency rule** (an architecture test parses every module's imports, ADR-0014): `schemas`, `use_cases` and
`i18n` → standard library (and `schemas`) only; `services` → also third-party; `api` wires everything;
`frontend` → only `backend.api`, `backend.schemas` and `i18n`.

## Contracts (internal API — the presenter of feature 005 consumes it)

```python
# backend/use_cases/ports.py
class FormatDetector(Protocol):
    def detect(self, path: Path) -> Detection | None: ...
        # Detection(format: FormatId, method: EXTENSION | CONTENT)

class ConversionRunner(Protocol):
    def convert(self, item: PlannedConversion, cancel: CancelToken) -> str: ...
        # returns Markdown; raises ConversionError(code: ErrorCode, detail: str) or Cancelled
    def close(self) -> None: ...

class SummaryWriter(Protocol):
    def write(self, root: OutputRootReport) -> None: ...

# backend/use_cases/planning.py, execution.py
def build_plan(inputs: Sequence[Path], *, recursive: bool, output_root: Path | None,
               detector: FormatDetector, limits: Limits,
               on_event: Callable[[BatchEvent], None] | None = None) -> BatchPlan

def execute_plan(plan: BatchPlan, *, overwrite: Callable[[PlannedConversion], bool],
                 runner: ConversionRunner, on_event: Callable[[BatchEvent], None],
                 cancel: CancelToken, clock: Clock) -> BatchReport

# backend/api/__init__.py — the facade
def plan_batch(inputs, *, settings, output_root=None, on_event=None) -> BatchPlan
def run_batch(plan, *, overwrite, settings, on_event, cancel) -> BatchReport  # also writes the summaries
```

- `BatchPlan` is immutable: planned conversions (source, target, detection, `exists`, `cost`), skipped items
  (path, `SkipReason`) and input errors, already **in execution order**. It is everything a GUI needs for its
  "review" step.
- **Deciding about existing outputs happens outside the backend:** the caller passes `overwrite`, a function
  answering per existing target (from the prompt, the flags or the settings; a GUI, from its dialog).
- `BatchReport` carries **data and codes, not text**: the summary writer turns it into words with the catalog
  (ADR-0012). `use_cases` never sees a catalog.
- Events are plain dataclasses; `on_event` runs in the caller's thread. Thread-hopping is the GUI's job
  (ADR-0001).

## The worker process (ADR-0015)

- `multiprocessing.get_context("spawn")` on every OS (the same behavior Windows will have), one `Process` with a
  duplex `Pipe`. Started on the first request, kept for the whole batch, closed by `run_batch`.
- The child ignores `SIGINT`, so Ctrl+C reaches only the CLI process, which decides what to stop.
- Requests: `("detect", path)` → `Detection | None`; `("convert", path, format)` → Markdown text, or an error
  code + detail. The child builds the registry once, through a **factory given as a dotted path** (spawn needs
  something importable): the real one from `composition`, a fake one from the tests.
- The supervisor waits with `conn.poll(0.1)` and, on every tick, checks:
  1. `cancel.is_set()` → kill the worker, raise `Cancelled`;
  2. elapsed > `limits.time_per_file` → kill, `timed_out`;
  3. `psutil.Process(pid).memory_info().rss` > `limits.worker_memory` → kill, `out_of_memory`;
  4. worker not alive → `worker_crashed`.
  The next request starts a new worker.
- `limits.worker_memory` = `min(psutil.virtual_memory().total // 2, 4 GiB)` by default.
- `freeze_support()` goes into the entry point when PyInstaller arrives (feature 006).

## Key rules (from ADR-0010, ADR-0015, ADR-0016 and the spec)

| Rule | Implementation |
|---|---|
| Output parent | file → `input.parent`; folder → `input.parent`, except a drive root (`p == p.parent`) or `Path.home()`, which use the folder itself; `--output-root` replaces it |
| Layout | `<output parent>/ClearMD_Output/Resumen_ClearMD.md` and `…/Output/`; a folder input goes to `Output/<input.name>/…`, a root/home input directly into `Output/` |
| Names | group targets by `str(path).casefold()`; in groups larger than one, every member gets `" (" + ext + ")"` (ext = source extension, or the detected format id when there is none); members still equal after that get `" (" + ext + " N)"`, N = 2, 3… in `casefold()` path order |
| Existing outputs | a target that exists on disk at planning time → `exists = True`; checked again just before writing |
| Skips | `ClearMD_Output` folders (casefold), symlinks (`is_symlink()` before `is_dir()`), hidden (`.` prefix; on Windows `st_file_attributes & FILE_ATTRIBUTE_HIDDEN`), `~$*`, `> limits.max_file_size`, `.md`/`.markdown`, `.zip`, suspicious archives, unsupported |
| Archive check | for ZIP-based formats, `zipfile.ZipFile(path).infolist()` reads only the central directory: sum of `file_size` > `limits.max_uncompressed` or `file_size / compress_size` > `limits.max_ratio` → skip `unsafe_archive`; an unreadable index is left to the converter (`corrupt_file`) |
| Cost and order | `cost = (uncompressed size if ZIP-based else st_size) × limits.weight[format]`; order by `(cost, casefold(path))` |
| Atomic write | write `target.with_name(target.name + ".clearmd-tmp")` → `os.replace(tmp, target)`; the temp file is removed on any failure or cancellation |
| Cancellation | the supervisor kills the worker at once; the current file is reported as cancelled, the rest too; the summaries are still written |
| Encoding | outputs and summary: UTF-8, LF line endings |

Names live in `schemas/formats.py`: `OUTPUT_DIR_NAME = "ClearMD_Output"`, `RESULTS_DIR_NAME = "Output"`,
`SUMMARY_NAME = "Resumen_ClearMD.md"`. Initial limits in `schemas/limits.py` (replaced by the benchmark, T07):
`max_file_size = 250 MiB`, `max_uncompressed = 1 GiB`, `max_ratio = 100`, `time_per_file = 600 s`, weights
`xlsx = 20`, `pdf = 4`, everything else `1`.

## Detection

1. `ExtensionDetector` (CLI process): a table of extensions → `FormatId` (`.pdf`, `.docx`, `.pptx`, `.xlsx`,
   `.html`/`.htm`, `.csv`, `.epub`, `.ipynb`, `.txt`).
2. Content detection (worker), **only** when the extension is missing or unknown: `Magika().identify_path()`,
   label → `FormatId` through a table verified against magika's real labels in T10. A result whose score is
   below magika's own default threshold counts as "unsupported".

## markitdown adapter (inside the worker only)

- One `MarkItDown(enable_plugins=False)` instance per worker (plugins could add network access, ADR-0005).
- `convert_local(str(path), stream_info=StreamInfo(extension=...))`: the detected format is passed as a hint, so
  extension-less files convert too. Returns `result.markdown`.
- Exception mapping:
  - `UnsupportedFormatException` → `unsupported_format`;
  - `FileConversionException` → inspect `attempts[*].exc_info`: a password error from pdfminer →
    `password_protected`; `zipfile.BadZipFile`, XML parse errors or pdfminer syntax errors → `corrupt_file`;
    anything else → `conversion_failed`;
  - `PermissionError` → `permission_denied`.

  The exact exception classes are confirmed with fixtures in T04, not assumed.
- `MissingDependencyException` must never happen: a test converts one fixture per format.

## Settings (read-only in this feature)

`platformdirs.user_config_path("ClearMD", appauthor=False) / "settings.toml"`:

```toml
language = "en"              # en | es                        (ADR-0017)
theme = "system"             # system | light | dark          (used by GUIs)
open_output_when_done = true # GUIs only; the CLI uses --open
on_existing_output = "ask"   # ask | overwrite | skip
recursive = true
html_strategy = "full"       # full | article                 (used from feature 004)
show_welcome = true          # GUIs only
```

Parsing with `tomllib` in `use_cases/settings.py`. An unknown key is ignored and an invalid value falls back to
its default; both produce a warning (AC-33). Serialization (needed by the settings window in 005) is
implemented and tested now, since it is plain formatting of flat scalars. The remembered output folder of the
GUIs is added in 005.

## i18n

- `en.toml` / `es.toml`: flat dotted keys (`cli.summary`, `error.password_protected.message`,
  `error.password_protected.action`, `summary.title`); `str.format` placeholders.
- `resolve_language(cli_lang, settings_lang)` → `"en" | "es"`, English when neither is set (ADR-0017).
- Parity test: same key set in both files, and the same placeholder names per key
  (`string.Formatter().parse`).

## CLI

```
clearmd [options] PATH [PATH ...]
  --no-recursive        only the top level of input folders
  --overwrite | --skip  what to do with outputs that already exist
  --output-root DIR     create ClearMD_Output inside DIR instead of next to each input
  --dry-run             show the plan, write nothing
  --open                open the output folder(s) when done
  --lang {en,es}        language for this run
  -q, --quiet           only the summary and errors
  --version
```

- Progress and prompts → stderr; the final summary → stdout. Exit codes as in AC-35.
- The prompt only appears when `sys.stdin.isatty()` and there are existing outputs to decide on.
- `--open`: `os.startfile` on Windows, `xdg-open` on Linux, `open` on macOS (local only, no network).
- `KeyboardInterrupt` → cancel token set → the supervisor stops the worker → summaries written → exit 130.

## Summary format (`Resumen_ClearMD.md`, shown in English)

```markdown
# ClearMD summary
2026-10-25 15:30 · ClearMD 0.1.0 · 12 converted · 2 skipped · 1 failed

## Converted
| Source | Output | Format |
|---|---|---|
| `project/notes.pdf` | `Output/project/notes.md` | PDF |
| `project/report.pdf` | `Output/project/report (pdf).md` | PDF |
| `project/Report.docx` | `Output/project/Report (docx).md` | DOCX |
| `project/scan` | `Output/project/scan.md` | DOCX, detected by content |

## Skipped
- `project/.cache/` — hidden folder

## Failed
- `project/contract.pdf` — This PDF is password-protected. Remove the password and try again.
  <details><summary>Technical detail</summary>PDFPasswordIncorrect: …</details>

<!-- clearmd:history -->
## History
- 2026-10-24 18:02 · 30 converted · 0 skipped · 0 failed
<!-- /clearmd:history -->
```

The writer reads only the lines between the history markers of the previous file. When the file is replaced,
the header line of the previous batch becomes the first history line.

## Testing strategy

- **Fixtures:** `tests/fixtures/build_fixtures.py` creates tiny documents reproducibly. pptx and xlsx use
  `python-pptx` and `openpyxl`, already installed through markitdown's extras. docx and EPUB are built as
  zip + XML by hand, PDF as minimal hand-written bytes, the encrypted PDF with `pypdf`, the corrupt files are
  truncated copies, and the zip bomb is a docx with a highly repetitive `document.xml` (small on disk). The
  generated files are committed (a few KB in total; marked binary in `.gitattributes`). `pypdf` joins the
  `dev` group only for this.
- **`tests/conftest.py`:** an autouse fixture that makes `socket.socket.connect` raise (AC-39). The worker is a
  separate process, so its tests install the same guard inside the child through the test registry factory.
- **Unit** (mirroring `src/`): table-driven `paths` tests (case-insensitive collisions, counters, Unicode, deep
  nesting, root/home, input-order shuffle); `archive` (bomb, ratio, unreadable index); `scanning` with
  `tmp_path` (symlinks, hidden, `~$`, `ClearMD_Output`, sparse 251 MiB file, missing inputs); `scheduling`;
  `planning`; `execution` with a fake runner (success, failure, cancellation, atomic write leaves no temp file);
  the worker with fake factories (slow → `timed_out`, memory hog → `out_of_memory`, `os._exit` →
  `worker_crashed`, cancellation mid-file); `settings` (missing, corrupt, invalid values); `i18n` parity;
  summary snapshots in both languages with a fixed clock, and history merging; the architecture import test.
- **Adapter:** the real markitdown on every fixture (one per format, plus password-protected and corrupt).
- **Acceptance:** `tests/acceptance/test_001_batch_conversion.py`, one test per AC, driving `cli.main(argv)` on
  `tmp_path`. Each slice adds the acceptance tests of the criteria it covers.
- **Benchmark** (`tests/benchmark/`, not part of the default `pytest` run): generated files of growing size
  per format; wall time and the worker's peak memory; worker start-up time; memory of a second magika instance.
  Results in `docs/benchmarks/001-conversion-limits.md`.
- **Gate:** `pytest`, `ruff check`, `ruff format --check`, `mypy --strict`, all inside the container.
