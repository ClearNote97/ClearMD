# ADR-0039: Modular layout and file size

- **Status:** proposed (accepted when refactor R01 closes its source phases, P11)
- **Date:** 2026-11-05
- **Supersedes:** the layout section of ADR-0014 (`<gui>/ … app/ views/ components/ layout/`), made
  exact here. ADR-0014's dependency rule stands.

## Context

ADR-0014 promised each GUI "the template's app/ views/ components/ layout/". It was not kept:
`ttk/app.py` grew to one 447-line class (585 lines), the presenter to 724 lines, the PDF reader to
1071, and the first Qt draft repeated the pattern. The owner's template (and their AgendNT-RX
project) reads differently: an entry file of a few lines, then small files with one concern each.
The owner does not want to read "kilometric" files.

## Decision

- **Size.** A `.py` file has at most **200 lines**, **250** as a hard limit, and the tolerance is not
  abused: at most 10 % of the files above 200; a class at most 150 lines; no mixins of ClearMD's own
  classes; a module under ~40 lines says in its docstring why it stands alone. A test enforces it
  over `src/`, `tests/` and `packaging/` (`tests/unit/test_module_size.py`), with a ratchet while R01
  runs: an oversized file may shrink, never grow, and no new one may appear.
- **One layout for every GUI** (`ttk`, `pyside`, later `flet`):

  ```
  <gui>/
    app.py        ≤ 40 lines: build the window and run it (the template's "app")
    window/       the window, split into small collaborators: the view the presenter draws on,
                  the user's intents, dialogs, closing; toolkit.py makes the toolkit's root
    layout/       how the rail, the working area and the action bar are arranged
    views/        one step per file (choose, review, convert, results); dialogs/ one per file
    components/   the pieces: rail, file list, figures, drop zone, action bar…
    visuals/      the toolkit's styles and drawings
  ```

  Each layer imports only the ones after it: `app.py` → `window/` → `views/` → `components/` →
  `visuals/`, `layout/` → `frontend.design`. A GUI may also import the presenter, `launch`,
  `schemas` and `i18n`; never `backend.api`, never another GUI.
- **Shared by every GUI:** `frontend/design/` (colours, measures: plain data) and `frontend/presenter/`
  (the logic: `intents/` what the user does, `screens/` what each step shows, `chrome/` the
  decisions every window repeats). The presenter never imports `design`.
- **Collaborators, not inheritance.** A collaborator receives only the widgets and ports it uses;
  none receives the whole window.
- **Re-exports** only in a package's `__init__`, public names only, with `__all__`; no shims.

## Consequences

- **Gains:** every file reads in one sitting; ttk, PySide6 and flet look alike inside, so a change in
  one shows where it goes in the others; the rule is checked, not remembered.
- **Costs:** more files and folders; the refactor itself (R01, 13 phases, no behaviour change, each
  step proved by byte-identical outputs and identical screenshots).
