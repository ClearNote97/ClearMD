# tests/fixtures — Sample documents

Small files created on purpose for the tests (never real documents, never personal data). They are committed:
they are part of the evidence that the converters work.

- `build_fixtures.py` runs the per-format builders in `builders/` and generates every document in `documents/` **reproducibly** (fixed ZIP timestamps, a
  fixed PDF file identifier). Each one carries a unique marker (`MARKERS`) that the tests look for in the
  converted Markdown.
- `test_fixtures.py` checks that the committed files match a fresh build and keep the properties the tests rely
  on (the PDF is encrypted, the corrupt files are unreadable, the zip bomb is small on disk and huge inside).

**Regenerate** (inside the container) after changing the builder, then commit the result:

```bash
uv run python tests/fixtures/build_fixtures.py
uv run pytest tests/fixtures
```
