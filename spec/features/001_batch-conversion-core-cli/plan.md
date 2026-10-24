# Plan — Feature 001: batch conversion, core + CLI

> The **how**. It must be executable without guessing. Criteria: [`spec.md`](./spec.md).

## Architecture

```
src/clearmd/
  core/                     # stdlib + clearmd.i18n only (enforced by a test)
    formats.py              # FormatId enum, extension table, reserved/skip-only extensions
    errors.py               # ErrorCode, SkipReason (each maps to a catalog key)
    models.py               # frozen dataclasses: Detection, PlannedConversion, SkippedItem, BatchPlan,
                            #   ConversionOutcome, BatchReport
    ports.py                # Protocols: DocumentConverter, FormatDetector
    cancel.py               # CancelToken (wraps threading.Event)
    events.py               # ScanProgress, ConversionStarted, ConversionFinished, BatchFinished
    paths.py                # pure: output_root_for(), target_for(), resolve_collisions()
    scanning.py             # expand inputs into candidates + skipped items
    planning.py             # build_plan()
    execution.py            # execute_plan(), atomic_write()
    report.py               # render_report() -> Markdown text
    settings.py             # Settings dataclass, defaults, parse/validate, serialize
  i18n/
    __init__.py             # Catalog, load_catalog(), resolve_language()
    en.toml, es.toml
  detection/
    extension.py            # ExtensionDetector (stdlib)
    content.py              # MagikaDetector (lazy import, single instance)
    chain.py                # ChainDetector: first non-None wins
  converters/
    markitdown_adapter.py   # MarkItDownConverter + exception mapping
    registry.py             # ConverterRegistry: FormatId -> DocumentConverter
  config/
    store.py                # settings path (platformdirs), load_settings()
  composition.py            # builds detector + registry; the only place that wires adapters
  cli/
    app.py                  # argparse, prompts, progress rendering, exit codes
```

**Dependency rule:** `core` imports only the standard library and `clearmd.i18n`. `detection`, `converters`
and `config` implement or feed the core's ports. `composition` wires everything; `cli` (and later the
presenter) only talks to `composition` and `core`. A unit test parses the imports of every `core` module and
fails on anything else.

## Contracts (internal API — the presenter of feature 005 consumes it)

```python
class DocumentConverter(Protocol):
    formats: frozenset[FormatId]
    def convert(self, source: Path, detection: Detection) -> str: ...
        # returns Markdown; raises ConversionError(code: ErrorCode, detail: str)

class FormatDetector(Protocol):
    def detect(self, path: Path) -> Detection | None: ...
        # Detection(format: FormatId, method: EXTENSION | CONTENT)

def build_plan(inputs: Sequence[Path], *, recursive: bool, output_root: Path | None,
               detector: FormatDetector, supported: frozenset[FormatId],
               on_event: Callable[[BatchEvent], None] | None = None) -> BatchPlan

def execute_plan(plan: BatchPlan, *, overwrite: Callable[[PlannedConversion], bool],
                 registry: ConverterRegistry, catalog: Catalog,
                 on_event: Callable[[BatchEvent], None], cancel: CancelToken) -> BatchReport
```

- `BatchPlan` is immutable and holds: planned conversions (source, target, detection, `exists: bool`),
  skipped items (path, `SkipReason`) and input errors. It is everything a GUI needs for its "review" step.
- **Deciding about existing outputs happens outside the core:** the caller passes `overwrite`, a function
  answering per existing target. The CLI builds it from the prompt, the flags or the settings; a GUI will
  build it from its dialog.
- Events are plain dataclasses; `on_event` runs in the core's thread. Thread-hopping is the GUI's job
  (ADR-0001).

## Key rules (from ADR-0010 and the spec)

| Rule | Implementation |
|---|---|
| Output root | file input → `input.parent`; folder input → `input.parent`, then `/<input.name>/…` inside the root; `--output-root` replaces the parent |
| Collisions | group targets by `str(path).casefold()`; groups larger than one, or a target equal to `clearmd-report.md`, get `" (" + source extension + ")"`; deterministic because sources are sorted by `casefold()` first |
| Existing outputs | a target that exists on disk at planning time → `exists = True` |
| Skips | `ClearMD_Output` folders (casefold), symlinks (`is_symlink()` before `is_dir()`), hidden (`.` prefix; on Windows `st_file_attributes & FILE_ATTRIBUTE_HIDDEN`), `~$*`, `> 250 MiB`, `.md`/`.markdown`, `.zip`, unsupported |
| Atomic write | write `target.with_name(target.name + ".clearmd-tmp")` → `os.replace(tmp, target)`; the temp file is removed on any failure or cancellation |
| Cancellation | checked before each file; Ctrl+C during a file aborts it (temp removed), marks the rest as cancelled, still writes the report |
| Encoding | outputs and report: UTF-8, LF line endings |

Constants live in `core/formats.py`: `OUTPUT_DIR_NAME = "ClearMD_Output"`, `REPORT_NAME = "clearmd-report.md"`,
`MAX_FILE_SIZE = 250 * 1024**2`.

## Detection

1. `ExtensionDetector`: a table of extensions → `FormatId` (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`/`.htm`,
   `.csv`, `.epub`, `.ipynb`, `.txt`).
2. `MagikaDetector`, **only** when the extension is missing or unknown: `Magika().identify_path()`, label →
   `FormatId` through a table verified against magika's real labels in task T08. Low-confidence results
   count as "unsupported".

## markitdown adapter

- One `MarkItDown(enable_plugins=False)` instance, created lazily and reused (plugins could add network
  access, ADR-0005).
- `convert_local(str(path), stream_info=StreamInfo(extension=...))`: the detected format is passed as a hint,
  so extension-less files convert too. Returns `result.markdown`.
- Exception mapping:
  - `UnsupportedFormatException` → `unsupported_format`;
  - `FileConversionException` → inspect `attempts[*].exc_info`: a password error from pdfminer →
    `password_protected`; `zipfile.BadZipFile`, XML parse errors or pdfminer syntax errors → `corrupt_file`;
    anything else → `conversion_failed`;
  - `PermissionError` → `permission_denied`.

  The exact exception classes are confirmed with fixtures in T09, not assumed.
- `MissingDependencyException` must never happen: a test converts one fixture per format.

## Settings (read-only in this feature)

`platformdirs.user_config_path("ClearMD", appauthor=False) / "settings.toml"`:

```toml
language = "auto"            # auto | en | es
theme = "system"             # system | light | dark          (used by GUIs)
open_output_when_done = true # GUIs only; the CLI uses --open
on_existing_output = "ask"   # ask | overwrite | skip
recursive = true
html_strategy = "full"       # full | article                 (used from feature 004)
show_welcome = true          # GUIs only
```

Parsing with `tomllib`. An unknown key is ignored and an invalid value falls back to its default; both
produce a warning (AC-26). Serialization (needed by the settings window in 005) is implemented and tested now
in `core/settings.py`, since it is plain formatting of flat scalars.

## i18n

- `en.toml` / `es.toml`: flat dotted keys (`cli.summary`, `error.password_protected.message`,
  `error.password_protected.action`, `report.title`); `str.format` placeholders.
- `resolve_language(cli_lang, settings_lang, os_locale)` → `"en" | "es"`. `os_locale` comes from
  `locale.getlocale()`; any `es*` → Spanish.
- Parity test: same key set in both files, and the same placeholder names per key
  (`string.Formatter().parse`).

## CLI

```
clearmd [options] PATH [PATH ...]
  --no-recursive        only the top level of input folders
  --overwrite | --skip  what to do with outputs that already exist
  --output-root DIR     write to DIR/ClearMD_Output instead of next to each input
  --dry-run             show the plan, write nothing
  --open                open the output folder(s) when done
  --lang {en,es}        language for this run
  -q, --quiet           only the summary and errors
  --version
```

- Progress and prompts → stderr; the final summary → stdout. Exit codes as in AC-28.
- The prompt only appears when `sys.stdin.isatty()` and there are existing outputs to decide on.
- `--open`: `os.startfile` on Windows, `xdg-open` on Linux, `open` on macOS (local only, no network).
- `KeyboardInterrupt` → cancel token set → report written → exit 130.

## Report format (`clearmd-report.md`, shown in English)

```markdown
# ClearMD report
2026-10-24 15:30 · ClearMD 0.1.0 · 12 converted · 2 skipped · 1 failed

## Converted
- `project/notes.pdf` → `project/notes.md` (PDF)
- `scan` → `scan.md` (DOCX, detected by content)

## Skipped
- `project/.cache/` — hidden folder

## Failed
- `project/contract.pdf` — This PDF is password-protected. Remove the password and try again.
  <details><summary>Technical detail</summary>PDFPasswordIncorrect: …</details>
```

## Testing strategy

- **Fixtures:** `tests/fixtures/build_fixtures.py` creates tiny documents reproducibly. pptx and xlsx use
  `python-pptx` and `openpyxl`, already installed through markitdown's extras. docx and EPUB are built as
  zip + XML by hand, PDF as minimal hand-written bytes, the encrypted PDF with `pypdf`, and the corrupt files
  are truncated copies. The generated files are committed (a few KB in total). `pypdf` joins the `dev` group
  only for this.
- **`tests/conftest.py`:** an autouse fixture that makes `socket.socket.connect` raise (AC-32).
- **Unit** (mirroring `src/`): table-driven `paths` tests (case-insensitive collisions, Unicode, deep nesting,
  reserved report name, input-order shuffle); `scanning` with `tmp_path` (symlinks, hidden, `~$`,
  `ClearMD_Output`, sparse 251 MiB file, missing inputs); `planning`; `execution` with a fake converter
  (success, failure, cancellation mid-batch, atomic write leaves no temp file); `settings` (missing, corrupt,
  invalid values); `i18n` parity; `report` snapshots in both languages; the architecture import test.
- **Adapter:** the real markitdown on every fixture (one per format, plus password-protected and corrupt).
- **Acceptance:** `tests/acceptance/test_001_batch_conversion.py`, one test per AC, driving `cli.main(argv)`
  on `tmp_path`.
- **Gate:** `pytest`, `ruff check`, `ruff format --check`, `mypy --strict`, all inside the container.
