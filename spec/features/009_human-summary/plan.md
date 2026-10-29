# Plan — Feature 009: A summary in human language, and its PDF

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0031.

- **`summary/content.py`:** the summary as data (headline, where, attention, converted, left out,
  kept, cancelled), built once from an `OutputRootReport`, in the catalog's language; shared by
  both writers.
- **`summary/writer.py`:** the Markdown from that data (code spans for names; the history kept,
  folded).
- **`summary/pdf_report.py`:** the PDF from the same data with PDFium (text objects in DejaVu
  Sans, filled shapes, wrapped text, pages).
- **Settings:** `summary_format`; the step-1 choice and the Settings row; `--summary-pdf`;
  `run_batch(summary_pdf=...)`.
- **Tests first;** golden summaries en/es; the PDF read back with PDFium; screenshots; reviews;
  v0.4.0.
