# ADR-0030: PDF read by PDFium and cleaned by ClearMD

- **Status:** accepted
- **Date:** 2026-10-29
- **Replaces, for PDF:** ADR-0004 (markitdown and pdfminer kept every other format).

## Context

The author converted two real PDFs with v0.1.0 (a published paper and a thesis, kept out of the
repository) and the Markdown was hard to use:
- words glued together, 161 per 1000 words in the paper ("interactionsbasedonvalues");
- `(cid:NN)` codes in place of the thesis's title page;
- rotated tables read backwards;
- running headers and page numbers mixed into the text;
- no headings at all.

The author proposed an experiment: would a cleaner over today's output be enough? It was measured
on both PDFs (feature 008, T01):

| | glued / 1000 words | `(cid)` codes | headers repeated | headings |
|---|---|---|---|---|
| today (pdfminer) | 160.8 · 0.0 | 0 · 291 | 74 · 180 | 0 · 0 |
| today + cleaner | 161.5 · 0.1 | 0 · 0 (deleted) | 40 · 154 | 0 · 0 |
| PDFium + cleaner | **0.4 · 0.1** | 0 · 0 (**read back**) | content only | 11 · 93 |

(paper · thesis). No cleaner gives back spaces that the extraction lost. pdfminer's `(cid:NN)` and
PDFium's `(6&8(/$…` are the same thing: a font embedded without a character map, whose glyph codes
are the letters moved by a fixed distance. PDFium also reads rotated text the right way round.

## Decision

- **PDFium reads** (`pypdfium2`, already bundled through markitdown, now a direct dependency):
  - text per character, with its font, size, weight and place;
  - in the worker process, like every converter (ADR-0015).
- **Glyph codes are read back per font.** A font whose space was moved to a control character,
  and whose other codes then become letters, is moved back. When the distance is 29 (the
  Macintosh standard glyph order of TrueType fonts), its accented letters are read from that
  order too. The summary says it happened.
- **ClearMD cleans.** Only text, no OCR and no tables rebuilt:
  - removes lines repeated at the top or bottom of many pages, and bare page numbers;
  - joins words broken at the end of a line, and the lines of a paragraph, also across a page;
  - holds a page's footnotes until the paragraph they cut ends;
  - finds headings by size (the tallest is level 1) or by a bold numbered line ("3.1 Data",
    "IV. RESULTS");
  - turns bullets into list items;
  - escapes all document text (ADR-0023).
- **What it could not do is told** (ADR-0022): pages without text (scanned), fonts read back,
  unreadable characters, running lines removed.
- markitdown no longer converts PDF: its `[pdf]` extra (pdfminer, pdfplumber) leaves the
  executable.

### After review (code review and security audit of 008)

- **A running line is one ClearMD is sure of.** Before removing it, ClearMD checks that it:
  - repeats at the same place and size on at least 30 % of the pages (never fewer than 3);
  - sits in the page's margin (its top or bottom 15 %), set apart from the text by a blank;
  - is not the size of a heading, and its text is in no page's body;
  - has numbers that are the same on every page or follow the pages.
- **Page numbers** count only as the first or last line in the margin, and only as a sequence
  across pages. Roman numerals must be valid ones. A document under 4 pages keeps everything.
- **Fonts are read back only when PDFium says they have no map.** A code with no letter is
  shown as "�" and counted, never dropped. That includes a code past the standard order and a
  font without a map that is not read back.
- **Memory and time:** two passes, the fonts' codes first, then one page at a time.
  - Measured on 20 MiB of text: 9 MiB of memory per MiB plain, 19 compressed; 6 s per MiB plain,
    14 compressed. The planning uses 16 MiB and 15 s per MiB.
  - A page with more than 200,000 characters keeps its first part, and the summary says so.
- **Bold** comes from the font's name or its ForceBold flag only. PDFium gives a font that
  declares no weight one from its stems, and plain Arial reads 695 (adversarial check).
  - A bold number starts a heading only where a block may start.
  - A "heading" followed in lowercase is the start of a sentence, and is turned back into text.
- **Fonts are told apart** by PDFium's own object (stable while the document is open), name and
  flags. A font has "no map" when most of its characters lack one.
- **List items are neutralized** like any line, and headings keep a final `#` (ADR-0023).
- ClearMD opens the document with PDFium's own call, so a load error is read when it happens; a
  PDF without pages is an empty document.

## Consequences

- Much better Markdown from typeset PDFs; faster (an 86-page thesis in under a second).
- The heuristics can misjudge a layout. A bold numbered line in a questionnaire becomes a heading.
  An accented capital past the standard order shows as "�", and the summary says so.
- PDFium has one reading order: a page in two columns may be read across.
- A hyphen at the end of a line is read as a broken word: "well-known" may read "wellknown" (a
  capital after it keeps the hyphen: "socio-Economic").
- Tables come out as lines of text; rebuilding them, and OCR, are out of scope.
- The executable is smaller (pdfminer and pdfplumber are gone).
