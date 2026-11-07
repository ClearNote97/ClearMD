# ttk/views/dialogs — One dialog per file

| Module | Role |
|---|---|
| `help.py` | `help_dialog`: how to use it, formats, where results go, privacy. |
| `welcome.py` | `WelcomeDialog`: the three steps and "Don't show again". |
| `settings.py` | `SettingsDialog`: the settings of ADR-0012; its rows scroll in a short window. |
| `split_settings.py` | `SplitSettings`: the "Split a PDF" group of the settings (023). |
| `keep_inputs.py` | `KeepInputsDialog`: keep the chosen files or start empty. |

All build on `components/dialog.py`. Import each from its module; this package re-exports nothing.
