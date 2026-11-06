# Feature 018 — The flet GUI

## Goal

The same app as the ttk and Qt windows — the same four steps, texts, choices and look — drawn by flet
(Flutter), on the same presenter, in the same layout (ADR-0039); delivered as a folder that carries
flet's own window program, so it never downloads anything (ADR-0042). With it, ClearMD offers its
three toolkits and becomes version 1.0.0.

## Scope

- **Includes:** the flet window (`frontend/flet`) at parity with Qt, except dropping files on the
  window (flet 1.0 cannot receive files from the system); its acceptance tests (the window built
  without a screen); its executable (`ClearMD-Flet`, a folder) built and checked by CI on Windows and
  Linux and released next to the others; a fourth part in the installer; screenshots; ADR-0042;
  version 1.0.0.
- **Does not include:** new conversion features; changes to the presenter's behaviour; choosing a
  main GUI (the owner's choice, after trying the three).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_018_*.py`) or a CI check.

- [x] **AC-01** `clearmd-flet` opens the window on the presenter: the rail with the logo, the four
  steps (each opens by click and Ctrl+1–4), the header, the texts from the catalogs in English and Spanish.
- [x] **AC-02** Choose: Add files / Add folder (native dialogs), the numbered list with icons, Remove
  selected / Clear all / Deselect all, the output choice (next to the originals or a folder), the
  summary format and the images choice; nothing listed twice. No drop on the window (flet 1.0 cannot):
  the empty list says to use the two buttons.
- [x] **AC-03** Review, Convert and Results show what the presenter gives: the figures, the plan's rows
  (skipped first, with what to do), the question about existing results, the progress (counter, file,
  bar, time left, long-file timer), the result's problems with the detail of the selected one.
- [x] **AC-04** The actions: Next/Convert/Open results with the reason when disabled, Back, Cancel while
  working, Convert more asking every time; Enter runs the primary action; a page change pauses it (F-1).
- [x] **AC-05** Help, the welcome (with "Don't show again") and Settings (exactly ADR-0012's settings,
  Restore defaults, Save applies at once); Esc closes a dialog.
- [x] **AC-06** Light and dark themes from the shared palette (`frontend/design`), following the system
  by default; every margin on the 8 px grid; body text at least 14 px; one primary action per page.
- [x] **AC-07** Closing while converting cancels and waits for the batch, so its summary is written.
- [x] **AC-08** A batch converted through the flet window gives the same Markdown as the CLI.
- [x] **AC-09** The executable: a folder `ClearMD-Flet/` with flet's window program inside (no download,
  no cache outside the folder), built and checked by CI (a real start with `--smoke`) on Windows and
  Linux, released as `ClearMD-Flet-<version>-windows.zip` and inside the Linux archive; the other
  executables carry no flet; the notices list flet and Flutter.
- [x] **AC-10** The installer offers the flet app as a fourth part, with its card and its own choice;
  CI installs, starts and removes it.
- [x] **AC-11** Screenshots of every screen, light and dark, English and Spanish, in
  `docs/screenshots/018/`, made by a script on CI.
- [x] **AC-12** ADR-0042; version 1.0.0; the READMEs and the release notes say how to get it.
