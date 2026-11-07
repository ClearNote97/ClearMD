# src/clearmd/frontend/ttk — The ttkbootstrap GUI (feature 005)

It draws what the presenter (`../presenter/`) gives it and forwards the user's intents (ADR-0026), in
ClearMD's look (ADR-0027). Layout of ADR-0039; each layer imports only the ones after it.

| Module | Role |
|---|---|
| `app.py` | The window and the presenter's `View`; `main()` is `clearmd-ttk`. |
| `presses.py`, `scheduler.py` | Press timing; `View.after`, safe from the worker thread. |
| `views/` | Home and one step per file (choose, review, convert, results); `dialogs/` one per file. |
| `components/` | The rail (and its drawing), the file list (and its keys), the cards, the drop zone, the start tiles. |
| `layout/` | The window's units (font sizes, start size) and its named fonts. |
| `visuals/` | Style names, themes, the styles, rounded buttons, Pillow shapes and marks. |
