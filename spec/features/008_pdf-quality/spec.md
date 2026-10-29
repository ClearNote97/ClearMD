# Feature 008 — PDF quality

## Goal

The PDFs the author converted with v0.1.0 gave Markdown that was hard to use: words glued together,
glyph codes in place of a title page, headers and page numbers in the text, no headings. A typeset
PDF must come out as readable Markdown, and what ClearMD could not read must be told (ADR-0030).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_008_pdf_quality.py`), on PDFs written
for the test. The author's two PDFs (`docs/Examples/`, never committed) are the yardstick: glued
words per 1000 went from 160.8 to 0.4.

### Reading
- [x] **AC-01** Words keep their spaces, and text drawn upside down reads the right way round.
- [x] **AC-02** Text in a font without a character map (glyph codes moved by a fixed distance) is
  read back, accented letters of the Macintosh standard order included, and the summary says so.
- [x] **AC-03** A page without text (a scan) is told by its number; ClearMD does no OCR.
- [x] **AC-04** A PDF with a password, or broken, fails with its reason, as before.

### Cleaning
- [x] **AC-05** Lines repeated at the top or bottom of many pages (headers, footers) and bare page
  numbers are left out, and the summary says so; in a short document (under 4 pages) nothing is.
- [x] **AC-06** Headings are found by their size (the tallest first) or by a bold numbered line
  ("1 Introduction", "3.1 Data", "IV. RESULTADOS"); a sentence or a formula is never one.
- [x] **AC-07** The lines of a paragraph are one paragraph; a blank, or a change of size, starts
  another; a paragraph goes on across a page when its sentence does, its page's footnotes after it.
- [x] **AC-08** A word broken at the end of a line is joined; bullets become list items.
- [x] **AC-09** Text from the document never becomes Markdown it did not write (ADR-0023).

### The product
- [x] **AC-10** markitdown no longer converts PDF (its pdfminer and pdfplumber are gone); the
  notes are in English and Spanish; the executable still converts PDF.

## Out of scope
- OCR of scanned pages; rebuilding tables; images and their captions as files.
