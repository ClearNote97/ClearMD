<!--
====================================================================
 ROADMAP  ·  spec/ (outside the Constitution)
--------------------------------------------------------------------
 Changes often; purpose, principles and stack do not.
 Orders the features (spec/features/NNN_...) in time.
====================================================================
-->

# Roadmap

A walking skeleton with the cheapest interface first: every new GUI reuses a core and a presenter that are
already tested (ADR-0001).

## Now

- [x] **Phase 0:** template pruning, `clearmd` package in the template layout, ADRs 0001–0018, UX contract,
      clean dev container.
- [ ] **001 — Batch conversion: backend + CLI** ([spec](./features/001_batch-conversion-backend-cli/spec.md)):
      worker process with limits, cost-ordered queue, detection, plan → confirm → execute,
      `ClearMD_Output/OutputMD/` + `Resumen_ClearMD.md` with history, markitdown adapter, i18n EN/ES, settings
      (read), complete CLI, benchmark.

## Next

- [ ] **002 — `.tex` converter** (subset defined in its spec; math preserved).
- [ ] **003 — `.odt` converter** (standard library only).
- [ ] **004 — HTML article mode** (second strategy for `.html`).
- [ ] **005 — Presenter (MVP) + ttkbootstrap GUI**, following `spec/contracts/ux.md`: help window, welcome,
      settings window, progress, splash, output folder choice (remembered).
- [ ] **006 — CI:** tests on Linux and Windows (Python 3.12 and 3.14) + executables in GitHub Releases;
      executable size as a metric; **code signing** of the Windows executables (SignPath, free for open
      source) so SmartScreen does not scare non-technical users.

## Later

- [ ] **007 — PySide6-Essentials GUI** (*onedir* distribution because of LGPL, ADR-0003).
- [ ] **008 — flet GUI.**
- [ ] Incremental mode: skip files unchanged since the last run.
- [ ] Minor formats: `.eml`, `.rtf`, subtitles.
- [ ] A second queue lane for heavy files, or parallel workers — only if the benchmark shows blocking
      (ADR-0015).
- [ ] Optional summary formats (e.g. PDF).
- [ ] **Publish on PyPI** (`pip install clearmd` / `uv tool install clearmd`), at the end (ADR-0018).

## Version 2

- [ ] **Tools window — Merge | Split** (ADR-0019):
      **Merge** `.md` files into one (`OutputUnif/`; the last batch by default, or any `.md` the user picks);
      **Split** a large source document into N similar parts in its own format (`OutputSep/`; PDF by pages
      first, then csv/txt and xlsx).
      From the plan review, a file marked too big or too slow (AC-42/43 of feature 001) offers **"Split it"**:
      Tools opens with a recommended number of parts (from the estimates, so each part fits the limits), and
      the parts replace the file in the batch when the user comes back.

## Out for now

See `spec/constitution/02_scope.md` → Out of scope: network/cloud, OCR, ZIP, image extraction, reverse
conversion, database, macOS.
