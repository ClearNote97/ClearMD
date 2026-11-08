# ttk/views/dialogs — One dialog per file

| Module | Role |
|---|---|
| `help.py` | `help_dialog`: how to use it, formats, where results go, privacy. |
| `welcome.py` | `WelcomeDialog`: the three steps and "Don't show again". |
| `settings.py` | `SettingsDialog`: the settings of ADR-0012; its rows scroll in a short window. |
| `split_settings.py` | `SplitSettings`: the Split group of the settings (023, 024). |
| `merge_settings.py` | `MergeSettings`: the "Merge Documents" group of the settings (026). |
| `keep_inputs.py` | `KeepInputsDialog`: "What Next?": keep the files, start empty, or go back Home. |

All build on `components/dialog.py`. Import each from its module; this package re-exports nothing.
