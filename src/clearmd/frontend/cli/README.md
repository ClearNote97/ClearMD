# src/clearmd/frontend/cli — Command-line interface

argparse, prompts, progress on stderr, summary on stdout, exit codes. The acceptance tests drive it.

| Module | What it holds |
|---|---|
| `__init__.py` | The package exports: `main`, `build_parser`. |
| `app.py` | `main(argv)`: the entry point and the last net (a message, never a traceback). |
| `parser.py` | `build_parser` and the language requested with `--lang`. |
| `flow.py` | `run`: settings, plan, decision, batch, summary, `--open`. |
| `prompts.py` | Whether anyone can answer, and the decision about existing outputs. |
| `progress.py` | The progress printer (stderr). |
| `report.py` | The summary, plan notes, settings warnings, dry run; printable names. |
| `batch.py` | Running the batch so Ctrl+C cancels it; the exit codes. |
