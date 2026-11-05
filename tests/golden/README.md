# tests/golden — The outputs refactor R01 must not change

`manifest.txt`: one SHA-256 per file ClearMD writes for the fixture corpora (`tests/fixtures/`), in
each output mode. `tests/acceptance/test_R01_golden.py` converts them again and compares.
Rewritten only on purpose, when an output is meant to change: `uv run python tests/support/golden.py`.
