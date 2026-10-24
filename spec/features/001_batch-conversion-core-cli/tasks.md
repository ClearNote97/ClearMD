# Tasks — Feature 001: batch conversion, core + CLI

> Executable steps, in order. Tick `[x]` when done. Test first: each task starts by writing the failing tests
> it names. Plan: [`plan.md`](./plan.md) · Criteria: [`spec.md`](./spec.md).

- [ ] **T01 — Fixtures.** `tests/fixtures/build_fixtures.py` + generated files (pdf, encrypted pdf, docx,
      pptx, xlsx, html, csv, epub, ipynb, txt, an extension-less docx, corrupt pdf/docx). Add `pypdf` to the
      `dev` group. Document in `tests/fixtures/README.md` how to regenerate them.
- [ ] **T02 — Test harness.** `tests/conftest.py` with the no-network autouse fixture (AC-32) and the
      architecture test that limits `core` imports to the standard library and `clearmd.i18n`.
- [ ] **T03 — Domain basics.** `core/formats.py`, `core/errors.py`, `core/models.py`, `core/ports.py`,
      `core/cancel.py`, `core/events.py`.
- [ ] **T04 — i18n.** `en.toml`, `es.toml`, `Catalog`, `resolve_language()`; parity test (keys +
      placeholders) (AC-24, AC-25).
- [ ] **T05 — Settings.** `core/settings.py` (defaults, validation, serialization) + `config/store.py`
      (platformdirs path, load); tests for missing, corrupt and invalid files (AC-26).
- [ ] **T06 — Output paths.** `core/paths.py`: output roots, targets, case-insensitive collisions, reserved
      report name, determinism (AC-01, AC-02, AC-04, AC-11, AC-12, AC-13, AC-21).
- [ ] **T07 — Scanning.** `core/scanning.py`: recursion, `ClearMD_Output`, symlinks, hidden, `~$`, size
      limit, `.md`/`.zip`, missing inputs (AC-02, AC-03, AC-05 – AC-08).
- [ ] **T08 — Detection.** `detection/extension.py`, `detection/content.py`, `detection/chain.py`. Verify
      magika's real labels for every supported format and write the mapping table from that (AC-09, AC-10).
      Measure the model's load time and note it in the plan.
- [ ] **T09 — markitdown adapter.** `converters/markitdown_adapter.py` + `converters/registry.py`. Confirm
      with the fixtures which exceptions mean "password" and "corrupt" before writing the mapping
      (AC-17, AC-18).
- [ ] **T10 — Planning.** `core/planning.py` + `ScanProgress` events; plan is identical for shuffled inputs.
- [ ] **T11 — Execution.** `core/execution.py`: per-file events, failure isolation, cancellation, atomic
      writes, existing-output decisions (AC-14, AC-17, AC-19, AC-20).
- [ ] **T12 — Report.** `core/report.py` in both languages; snapshot tests (AC-22).
- [ ] **T13 — Composition root.** `composition.py` building the detector chain and the registry.
- [ ] **T14 — CLI.** Arguments, prompt, progress, summary, `--dry-run`, `--open`, `--output-root`,
      `--lang`, `--quiet`, exit codes (AC-15, AC-16, AC-23, AC-27 – AC-31).
- [ ] **T15 — Acceptance tests.** `tests/acceptance/test_001_batch_conversion.py`, one test per AC-01 … AC-32.
- [ ] **T16 — Close the feature.**
  - Update `docs/architecture/README.md` to the as-built design.
  - Add usage to `README.md` and `README.es.md`.
  - Tick the roadmap.
  - Pass the gate (pytest, ruff, mypy strict).
  - Review by `code-reviewer`, and by `security-auditor` (untrusted files and paths).
  - Any new non-trivial decision becomes an ADR.
