# pyside/window — The window and its collaborators

`window.py` is the composition root and the presenter's `View`: it builds the pieces below and
forwards every `View` call to the one that does it. None of them receives the whole window.

| Module | Role |
|---|---|
| `window.py` | `PySideApp`: wiring, one-line `View` forwards; a plain object that owns the widget. |
| `qt_window.py` | `MainWindow(QWidget)`: Qt's close, resize and drag hooks, each a forward to a callback. |
| `view.py` | What the `View` calls do to the widgets (`PySideView`). |
| `frame.py` | The widgets and their arrangement (rail, surface, step views, action bar). |
| `controls.py` | Which widgets a state enables; the compact and short layouts. |
| `offer.py` | Which "Split the Large PDFs (N)" the action bar offers on Review and Results (025). |
| `shown.py` | What the window shows now (state, plan, result, language, theme, scan). |
| `dialog_host.py` | One dialog at a time: help, settings, welcome, Convert more. |
| `primary_button.py` | The primary press and its pause after a page change. |
| `inputs.py` | Enter, Ctrl+1..4, Delete and dropped files. |
| `pickers.py` | The native pickers: Add files, Add folder, output folder. |
| `closing.py` | Closing, and waiting for a batch to end. |
| `toolkit.py` | The `QApplication`: its name, icon and font. |
| `scheduler.py` | `View.after` for Qt: a queued signal, safe from any thread. |

Imports `views/`, `components/`, `layout/`, `visuals/` and the presenter; never the entry file.
