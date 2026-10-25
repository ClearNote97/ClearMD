# Tasks — Feature 001: batch conversion, backend + CLI

> Executable steps, in order, grouped in **vertical slices**: each slice ends with something that runs end to
> end and with the acceptance tests of the criteria it covers. Tick `[x]` when done. Test first: each task
> starts by writing the failing tests it names. Plan: [`plan.md`](./plan.md) · Criteria: [`spec.md`](./spec.md).

## Slice A — Walking skeleton: one file, end to end, through the worker

Goal: `clearmd D/report.pdf` writes `D/ClearMD_Output/Output/report.md` through the real worker process. It
brings the two riskiest parts (the worker and markitdown) to the front.

- [ ] **T01 — Fixtures.** `tests/fixtures/build_fixtures.py` + generated files (pdf, encrypted pdf, docx,
      pptx, xlsx, html, csv, epub, ipynb, txt, an extension-less docx, corrupt pdf/docx, a zip-bomb docx).
      Add `pypdf` to the `dev` group. Document in `tests/fixtures/README.md` how to regenerate them.
- [ ] **T02 — Test harness.** `tests/conftest.py` with the no-network autouse fixture (AC-39) and the
      architecture test of ADR-0014 (imports per package).
- [ ] **T03 — Schemas and i18n basics.** `schemas/formats.py`, `limits.py`, `errors.py`, `models.py`,
      `events.py`; `use_cases/ports.py`, `cancel.py`; `i18n/` with `Catalog`, `resolve_language()` and the
      keys this slice needs; parity test (AC-31, AC-32).
- [ ] **T04 — markitdown adapter.** `services/conversion/markitdown_adapter.py` + `registry.py`. Confirm with
      the fixtures which exceptions mean "password" and "corrupt" before writing the mapping (AC-22).
- [ ] **T05 — Worker process.** `services/worker/` (protocol, child, supervisor): persistent worker, time
      and memory limits, cancellation, replacement after a kill or a crash (AC-19, AC-23 – AC-26 at unit level).
- [ ] **T06 — Thin path to the CLI.** `use_cases/paths.py` for a single file, `use_cases/execution.py` with
      atomic writes, `api/` (`plan_batch`, `run_batch`, `composition.py`) and a minimal CLI with progress,
      summary line and exit codes 0/1/2 (acceptance: AC-01, AC-19, AC-21, AC-22).
- [ ] **T07 — Benchmark.** `tests/benchmark/` (deselected from the default run with a `benchmark` marker):
      time and peak memory per format and size, worker start-up, memory of a second magika instance. Write
      `docs/benchmarks/001-conversion-limits.md`; update `schemas/limits.py` (limits and weights) and the
      spec/ADR-0015 values if they change.

## Slice B — Folders and untrusted input

- [ ] **T08 — Scanning.** `use_cases/scanning.py`: recursion, `ClearMD_Output`, symlinks, hidden, `~$`, size
      limit, `.md`/`.zip`, missing inputs, empty inputs (AC-02, AC-03, AC-05 – AC-08).
- [ ] **T09 — Archive check.** `use_cases/archive.py`: uncompressed size and ratio from the central
      directory; the zip-bomb fixture is skipped without being decompressed (AC-09).
- [ ] **T10 — Detection.** `services/detection/extension.py`, `chain.py` and the content detector served by
      the worker. Verify magika's real labels for every supported format and write the mapping from that
      (AC-10, AC-11).

## Slice C — Plan, names, order and the summary

- [ ] **T11 — Output paths and names.** `use_cases/paths.py` complete: output parents, root/home, layout,
      `--output-root`, case-insensitive collisions with extension and counter, determinism
      (AC-04, AC-12 – AC-15).
- [ ] **T12 — Planning and scheduling.** `use_cases/planning.py` + `scheduling.py` + `ScanProgress` /
      `PlanReady` events; the plan is identical for shuffled inputs and ordered by cost (AC-20).
- [ ] **T13 — Execution complete.** Existing outputs (re-checked before writing), failure isolation,
      cancellation, permission errors per output root (AC-16, AC-21, AC-26, AC-27).
- [ ] **T14 — Summary.** `services/summary/writer.py`: name table, skipped, failed, cancelled, history merge,
      both languages; snapshot tests with a fixed clock (AC-28, AC-29).

## Slice D — Language, settings and the complete CLI

- [ ] **T15 — Settings.** `schemas/settings.py`, `use_cases/settings.py` (defaults, validation,
      serialization) + `services/settings_store.py` (platformdirs path, load); tests for missing, corrupt and
      invalid files (AC-33, AC-34).
- [ ] **T16 — CLI complete.** Prompt, `--overwrite`/`--skip`, `--dry-run`, `--open`, `--output-root`,
      `--lang`, `--quiet`, `--no-recursive`, exit codes 3 and 130 (AC-17, AC-18, AC-30, AC-31, AC-34 – AC-38).
- [ ] **T17 — Acceptance sweep.** `tests/acceptance/test_001_batch_conversion.py` covers AC-01 … AC-39, one
      test per criterion; add the ones not written in earlier slices.
- [ ] **T18 — Close the feature.**
  - Update `docs/architecture/README.md` to the as-built design.
  - Add usage to `README.md` and `README.es.md`.
  - Tick the roadmap.
  - Pass the gate (pytest, ruff, mypy strict).
  - Review by `code-reviewer`, and by `security-auditor` (untrusted files, paths, archives, the worker).
  - Any new non-trivial decision becomes an ADR.
