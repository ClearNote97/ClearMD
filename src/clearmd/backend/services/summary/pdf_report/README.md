# summary/pdf_report — Resumen_ClearMD.pdf

The summary in the app's look (ADR-0031, ADR-0027), drawn with PDFium in Helvetica: nothing embedded, no link,
no action. The same `SummaryContent` as the Markdown.

| Module | Role |
|---|---|
| `theme.py` | Page measures, the light palette, `Run` (text in one style). |
| `metrics.py` | Text widths by PDFium: ink, per-character advances (the one cache), `width`, `cut`. |
| `text.py` | Windows Latin only, names from the user's files, `wrap`, `fit`. |
| `canvas.py` | `Canvas`: pages, text, rectangles, circles, `save`. |
| `table.py` | The converted files as a table with a repeating header. |
| `blocks.py` | `Blocks`: band, headline, headings, paragraphs, entries, note descriptions. |
| `report.py` | `PdfReport`: `write`, `render`. |

Imports: `theme` <- `metrics` <- `text` <- `canvas` <- `table`, `blocks` <- `report`.
