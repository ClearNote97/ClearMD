# ttk/window — The window and its collaborators

`window.py` is the composition root and the presenter's `View`: it builds the pieces below and
forwards every `View` call to the one that does it. None of them receives the whole window.

| Module | Role |
|---|---|
| `window.py` | `TtkApp`: wiring, the public attributes, one-line `View` forwards. |
| `view.py` | What the `View` calls do to the widgets (`TtkView`). |
| `frame.py` | The widgets and their arrangement (rail, surface, Home and step views, action bar). |
| `home_chrome.py` | Home has no action bar nor message at its foot (023). |
| `controls.py` | Which buttons a state enables; the compact and short layouts. |
| `shown.py` | What the window shows now (state, plan, result, language, theme, page). |
| `dialog_host.py` | One dialog at a time: help, settings, welcome, Convert more. |
| `primary_button.py` | The primary press and its pause after a page change. |
| `inputs.py` | Enter, space, Ctrl+0 (Home) and Ctrl+1..4, and dropped files (`presses.py` counts a held key once). |
| `pickers.py` | The native pickers: Add files, Add folder, output folder. |
| `closing.py` | Closing, and waiting for a batch to end. |
| `toolkit.py` | The Tk root (with drag and drop), its style, fonts, look and icons. |
| `scheduler.py` | `View.after` for Tk, safe from any thread. |

Imports `views/`, `components/`, `layout/`, `visuals/` and the presenter; never the entry file.
