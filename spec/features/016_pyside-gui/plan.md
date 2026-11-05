# Plan — Feature 016: The PySide6 GUI

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0003 (PySide6-Essentials, LGPL),
> ADR-0026 (presenter), ADR-0027 (identity), ADR-0038 (delivery), ADR-0039 (layout).

## Where things are

`src/clearmd/frontend/pyside/` already has the layout of ADR-0039 (refactor R01): `app.py` →
`window/` (view, dialog host, primary button, inputs, pickers, closing, the Qt main window and its
scheduler) → `views/` → `components/` → `visuals/`, `layout/`. Its decisions come from
`presenter/chrome/`; its tokens from `frontend/design/`.

## Work

1. **Parity and acceptance** — `tests/acceptance/test_016_*.py`, offscreen (`QT_QPA_PLATFORM`), with
   the presenter's fake backend (`tests/support/gui_fakes.py`) and, for AC-08, the real one. Gaps found
   by the tests are fixed in the window, never in the presenter.
2. **Packaging** — `packaging/clearmd_pyside.spec`: a onedir `ClearMD-Qt` (`exclude_binaries` +
   `COLLECT`), the other GUIs and their toolkits excluded, the ttk spec unchanged;
   `packaging/launch_pyside.py`; `check_executables.sh` starts it with `--smoke` and caps its size;
   `package.sh` zips it on Windows and puts it in the Linux archive; the release workflow builds both.
3. **Screenshots** — `tests/gui/pyside_screenshots.py` (offscreen `grab()`), `docs/screenshots/016/`.
4. **Docs** — ADR-0038, README rows and "How to run", release notes, version 0.11.0.
