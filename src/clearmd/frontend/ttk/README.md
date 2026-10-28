# src/clearmd/frontend/ttk — The ttkbootstrap GUI (feature 005)

It draws what the presenter (`../presenter/`) gives it and forwards the user's intents (ADR-0026), in
ClearMD's look (ADR-0027).

| Module | Role |
|---|---|
| `app.py` | The window and the presenter's `View`; `main()` is `clearmd-ttk`. |
| `scheduler.py` | `View.after`, safe from the worker thread (a queue the UI thread empties). |
| `layout.py` | The 8 px grid, the font sizes (14 px body), the window's sizes. |
| `brand.py` | The palette, the `clearmd-light` / `clearmd-dark` themes, rounded buttons and cards. |
| `art.py` | Pillow drawings: rounded shapes, the background shape, a list row's number and icon. |
| `views/` | The screens: main, plan, progress, result; help, welcome, settings. |
| `components/` | The rail (logo, steps), the working area, the drop zone, the numbered file list. |
