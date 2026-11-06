# src/clearmd/frontend/flet — The flet GUI (feature 018)

It draws what the presenter (`../presenter/`) gives it and forwards the user's intents (ADR-0038),
in ClearMD's look (ADR-0027), with flet (Flutter). The same layout as `../ttk/` and `../pyside/`
(ADR-0039); each layer imports only the ones after it.

The window is built on a page port (`window/page_port.py`): flet's controls are plain objects, so
the whole window is built and driven without flet's program (tests, no screen). flet 1.0 cannot
receive files dropped from the system: there is no drop zone; the empty list says to use the
two buttons.

| Module | Role |
|---|---|
| `app.py` | `main()` is `clearmd-flet`: `ft.run` with the assets folder; the window on its page. |
| `window/` | `FletApp` (the presenter's `View`, a plain object), the page port and the collaborators. |
| `views/` | One step per file (choose, review, convert, results); `dialogs/` one per file. |
| `components/` | The rail, the file list, the cards, the action bar, the dialog base. |
| `layout/` | The window's own sizes (a step's height, the badge, the list's columns, the dialogs). |
| `visuals/` | The theme from the shared palette, the texts' and buttons' look, the pictures. |
