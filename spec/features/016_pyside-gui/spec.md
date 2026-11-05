# Feature 016 — The PySide6 GUI

## Goal

The same app as the ttk window — the same four steps, texts, choices and look — drawn by Qt
(PySide6-Essentials, ADR-0003), on the same presenter, in the same layout (ADR-0039); delivered as a
folder the user unzips and opens (LGPL, ADR-0038).

## Scope

- **Includes:** the PySide6 window (`frontend/pyside`, started in refactor R01) brought to parity with
  ttk; its acceptance tests; its executable (`ClearMD-Qt`, a folder) built and checked by CI on Windows
  and Linux and released next to the ttk app; screenshots; ADR-0038.
- **Does not include:** new conversion features; changes to the presenter's behaviour; flet (017);
  choosing a main GUI (after 017, the owner's choice).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_016_*.py`); the window runs offscreen.

- [ ] **AC-01** `clearmd-pyside` opens the window on the presenter: the rail with the logo, the four
  steps (each opens by click and Ctrl+1–4), the header, the texts from the catalogs in English and Spanish.
- [ ] **AC-02** Choose: Add files / Add folder (native dialogs), files dropped on the window, the
  numbered list with icons, Remove selected / Clear all / Deselect all, the output choice (next to the
  originals or a folder), the summary format and the images choice; nothing listed twice.
- [ ] **AC-03** Review, Convert and Results show what the presenter gives: the figures, the plan's rows
  (skipped first, with what to do), the question about existing results, the progress (counter, file,
  bar, time left, long-file timer), the result's problems with the detail of the selected one.
- [ ] **AC-04** The actions: Next/Convert/Open results with the reason when disabled, Back, Cancel while
  working, Convert more asking every time; Enter runs the primary action, held down once; a page change
  pauses it (F-1).
- [ ] **AC-05** Help, the welcome (with "Don't show again") and Settings (exactly ADR-0012's settings,
  Restore defaults, Save applies at once); Esc closes a dialog.
- [ ] **AC-06** Light and dark themes from the shared palette (`frontend/design`), following the system
  by default; every margin on the 8 px grid; body text at least 14 px; one primary action per page.
- [ ] **AC-07** Closing while converting cancels and waits for the batch, so its summary is written.
- [ ] **AC-08** A batch converted through the PySide6 window gives the same Markdown as the CLI.
- [x] **AC-09** The executable: a folder `ClearMD-Qt/` (PySide6 replaceable, LGPL) built and checked by
  CI (a real start with `--smoke`) on Windows and Linux, released as `ClearMD-Qt-<version>-windows.zip`
  and inside the Linux archive; the ttk app and the CLI still carry no Qt; the notices list PySide6.
- [ ] **AC-10** Screenshots of every screen, light and dark, English and Spanish, in
  `docs/screenshots/016/`, made by a script.
- [ ] **AC-11** ADR-0038; version 0.11.0; the READMEs say how to get it.
