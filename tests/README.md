# tests/ — Verification (the gate)

Nothing counts as done until it passes here. Every fixed bug first gets a test that reproduces it.
Always cover: **happy path + edge cases + empty state**. Run inside the container: `uv run pytest`.

| Folder | Role |
|---|---|
| `unit/` | Unit tests of the `clearmd` package (core, converters, presenter, CLI). |
| `acceptance/` | Acceptance tests **per feature**, one per criterion of its `spec.md` (`AC-NN`). |
| `fixtures/` | Small sample documents (pdf, docx, tex, odt, html…) used by the tests. |
