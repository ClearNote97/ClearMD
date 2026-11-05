# conversion/pdf — The PDF converter (features 008, 013–015)

PDFium reads the characters and drawings (ADR-0030); ClearMD rebuilds lines, paragraphs, tables
and equations from where they stand. Laid out by refactor R01 (ADR-0039).

| Module / package | What |
|---|---|
| `reader.py` | `read()`: one document, page by page, within the limits (`MAX_DOCUMENT_PIXELS`, `MAX_CROPS`) |
| `model.py`, `decode.py` | The data a page becomes (lines, words, glyph boxes); characters decoded from fonts without a map |
| `pdfium/` | Everything that talks to PDFium: the document, fonts, characters, drawings, pictures, crops |
| `lines/` | Characters → words → lines; sub- and superscripts |
| `blocks/` | A page's tables and equations placed among its lines; equations as LaTeX |
| `tables/`, `lattice.py` | Tables found by their text's columns (stream) and by their rules (lattice) |
| `equations/` | Display equations found by their number or their fraction bar |
| `latex/` | An equation's pieces rebuilt as LaTeX (ADR-0036) |
| `cleaner/` | Lines → Markdown: running headers, page numbers, paragraphs, headings, footnotes |
