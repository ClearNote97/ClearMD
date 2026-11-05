# ttk/window — The window and its collaborators

| Module | Role |
|---|---|
| `toolkit.py` | The Tk root (with drag and drop), its style, its icons. |
| `scheduler.py` | `View.after` for Tk, safe from any thread. |
| `presses.py` | A key held down is one press. |

Imports `views/`, `components/`, `layout/`, `visuals/` and the presenter; never the entry file.
