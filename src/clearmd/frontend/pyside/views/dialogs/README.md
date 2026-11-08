# pyside/views/dialogs — One dialog per file

| Module | Role |
|---|---|
| `help.py` | `HelpDialog`: how to use it, formats, where results go, privacy. |
| `welcome.py` | `WelcomeDialog`: the three steps and "Don't show again". |
| `settings.py` | `SettingsDialog`: the settings of ADR-0012. |
| `split_settings.py` | `SplitSettings`: the dialog's Split a PDF group (feature 023). |
| `what_next.py` | `WhatNextDialog`: Results' "What Next?": the three tools as small tiles, Keep the files (033). |

All build on `components/dialog.py`. Import each from its module; this package re-exports nothing.
