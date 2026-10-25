# tests/ — Verification (the gate)

Nothing counts as done until it passes here. Every fixed bug first gets a test that reproduces it.
Always cover: **happy path + edge cases + empty state**. Run inside the container: `uv run pytest`.

| Folder / file | Role |
|---|---|
| `unit/` | Unit tests, a mirror of `src/clearmd/`, plus the architecture test of ADR-0014. |
| `acceptance/` | Acceptance tests **per feature**, one per criterion of its `spec.md` (`AC-NN`). |
| `fixtures/` | Generated sample documents and the script that builds them reproducibly. |
| `support/` | Helpers shared by the tests: the network guard and the fixture paths. |
| `conftest.py` | Autouse fixture that makes every network connection fail (ADR-0005, AC-39). |
