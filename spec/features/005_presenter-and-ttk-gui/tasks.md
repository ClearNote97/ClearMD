# Tasks — Feature 005: Presenter (MVP) + ttkbootstrap GUI

> Executable steps, in order, in vertical slices; each slice ends with something that runs end to end and the
> acceptance tests of the criteria it covers. Test first. Plan: [`plan.md`](./plan.md) · Criteria:
> [`spec.md`](./spec.md).

## Slice A — The presenter, without a window

- [x] **T01 — Environment.** Tk, `xvfb` and fonts in the dev container (`Dockerfile`, ADR-0008);
      `ttkbootstrap` and `tkinterdnd2` pinned (two weeks old at least); the architecture rules for
      `presenter/` and `ttk/`.
- [x] **T02 — Settings written, folders opened.** `save_settings`, `last_output_folder`, `open_folder` shared
      (AC-06, AC-15).
- [ ] **T03 — The presenter.** States, intents, worker thread and scheduler, texts from the catalogs, the system
      theme; tested with a fake view and a fake backend (AC-01 – AC-04, AC-06 – AC-12, AC-16).

## Slice B — The window

- [ ] **T04 — The ttk shell and the main view.** Theme, layout constants, Add files / Add folder / drag and drop
      / input list / output choice / Convert / "?" / settings; `clearmd-ttk` (AC-05, AC-16, AC-17, AC-20).
- [ ] **T05 — Plan, progress, result.** The three views on the presenter's models; Cancel; Open results folder
      (AC-07 – AC-12).
- [ ] **T06 — Help, welcome, settings.** The three dialogs (AC-13 – AC-15).
- [ ] **T07 — Keyboard and look.** Tab order, Enter, Esc, nothing only on hover, both themes checked (AC-17 –
      AC-19).

## Slice C — Shown and closed

- [ ] **T08 — Screenshots.** The script under xvfb; `docs/screenshots/005/` (AC-21).
- [ ] **T09 — Acceptance and a real batch.** `tests/acceptance/test_005_ttk_gui.py`, one test per AC-01 … AC-21;
      the same outputs as the CLI (AC-20).
- [ ] **T10 — Close the feature.** READMEs (with the screenshots), architecture, roadmap, spec ticked; gate;
      code review, security audit with runnable proofs, adversarial verification of the fixes; ADR-0026
      accepted. Then the repository becomes public (the author's request), after a scan of the whole history.
