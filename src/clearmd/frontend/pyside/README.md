# src/clearmd/frontend/pyside — The PySide6 GUI (feature 016)

It draws what the presenter (`../presenter/`) gives it and forwards the user's intents (ADR-0038),
in ClearMD's look (ADR-0027). The same layout as `../ttk/` (ADR-0039); each layer imports only the
ones after it.

| Module | Role |
|---|---|
| `app.py` | `main()` is `clearmd-pyside`: the application, the window, `exec()`. |
| `window/` | `PySideApp` (the presenter's `View`, a plain object), `MainWindow` (Qt's hooks) and the collaborators. |
| `views/` | One step per file (choose, review, convert, results); `dialogs/` one per file. |
| `components/` | The rail (and its drawing), the file list, the cards, the drop zone, the dialog base. |
| `layout/` | The window's own sizes (a step's height, the badge, the file icon). |
| `visuals/` | The style sheet and the pictures. |
