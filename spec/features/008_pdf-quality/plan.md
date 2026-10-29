# Plan — Feature 008: PDF quality

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0030.

- **Experiment first (T01):** cleaner-only against PDFium + cleaner on the author's two PDFs, with
  the same metrics (glued words, `(cid)` codes, reversed lines, repeated lines, headings).
- **`conversion/pdf/reader.py`:** PDFium per character (font handle, size from the loose box,
  weight or bold name, place); lines; glyph codes moved back per font; surrogate pairs joined.
- **`conversion/pdf/cleaner.py`:** running lines, page numbers, body size, heading levels, a block
  writer (headings, list items, paragraphs, held footnotes), hyphenation, escaping and
  neutralizing (ADR-0023).
- **`conversion/pdf/__init__.py`:** the converter, PDFium's load errors mapped, the four notes.
- **Registry** routes PDF to it; markitdown loses its `[pdf]` extra; `pypdfium2` is direct.
- **Tests first** on PDFs written by `tests/support/pdf_builder.py`; the acceptance file; reviews;
  v0.3.0.
