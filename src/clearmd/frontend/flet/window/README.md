# flet/window — The window and its collaborators

`window.py` is the composition root and the presenter's `View`: it builds the pieces below and
forwards every `View` call to the one that does it. None of them receives the whole window.

| Module | Role |
|---|---|
| `window.py` | `FletApp`: wiring, one-line `View` forwards; a plain object on a page port. |
| `page_port.py` | `PagePort`: what the window needs from flet's page; `KeyPress`. |
| `flet_page.py` | `FletPage`: the port on flet's real page (window, picker, loop, keyboard). |
| `toolkit.py` | `open_window(page)`: what `ft.run` calls; the smoke run's close. |
| `view.py` | What the `View` calls do to the controls (`FletView`). |
| `frame.py` | The controls and their arrangement (rail, surface, step views, action bar). |
| `controls.py` | Which controls a state enables; the compact rail. |
| `shown.py` | What the window shows now (state, plan, result, language, theme, scan). |
| `dialog_host.py` | One dialog at a time: help, settings, welcome, Convert more. |
| `primary_button.py` | The primary press and its pause after a page change. |
| `keys.py` | Enter, Esc, Ctrl+1..4, Delete and Ctrl+A. |
| `focus.py` | Which control has the keyboard focus (a number field too): Enter is its own then. |
| `pickers.py` | The system's pickers: Add files, Add folder, output folder. |
| `closing.py` | Closing, and waiting for a batch to end. |
| `scheduler.py` | `View.after` for flet: queued to the page's loop, safe from any thread. |

Imports `views/`, `components/`, `layout/`, `visuals/` and the presenter; never the entry file.
