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

- [x] **Phase 0:** template pruning, `clearmd` package, ADRs 0001–0013, UX contract, clean dev container.
- [ ] **001 — Batch conversion: core + CLI** ([spec](./features/001_batch-conversion-core-cli/spec.md)):
      detection, plan → confirm → execute, `ClearMD_Output`, report, markitdown adapter, i18n EN/ES, settings
      (read), complete CLI.

## Next

- [ ] **002 — `.tex` converter** (subset defined in its spec; math preserved).
- [ ] **003 — `.odt` converter** (standard library only).
- [ ] **004 — HTML article mode** (second strategy for `.html`).
- [ ] **005 — Presenter (MVP) + ttkbootstrap GUI**, following `spec/contracts/ux.md`: help window, welcome,
      settings window, progress, splash.
- [ ] **006 — CI:** tests on Linux and Windows + executables in GitHub Releases; executable size as a metric.

## Later

- [ ] **007 — PySide6-Essentials GUI** (*onedir* distribution because of LGPL, ADR-0003).
- [ ] **008 — flet GUI.**
- [ ] Incremental mode: skip files unchanged since the last run.
- [ ] Minor formats: `.eml`, `.rtf`, subtitles.

## Out for now

See `spec/constitution/02_scope.md` → Out of scope: network/cloud, OCR, ZIP, image extraction, reverse
conversion, database, macOS.
