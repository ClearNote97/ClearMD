# Feature 027 — Split more formats: text, CSV and Excel

## Goal

Split takes plain text, CSV and Excel too, by whole lines, rows or sheets, in their own format.
As always, nothing inside them changes (ADR-0043, ADR-0047).

## Acceptance criteria (what MUST be true)

- [x] **AC-01** **Text** (`.txt`) is cut at line breaks, never inside a line:
  - into N parts, balanced by words; or
  - into parts of about N words.

  The parts, put back together, are the file. "Every N pages" leaves it out with a reason.
- [x] **AC-02** **CSV** (`.csv`) is cut between rows, never inside a quoted field that spans
  lines:
  - into N parts; or
  - parts of about N words.

  Every part starts with the file's header row, so each part is a valid table with its column
  names. The rows, in order, are the file's rows.
- [x] **AC-03** **Excel** (`.xlsx`) is cut by whole sheets: "into N parts" groups the sheets, in
  order, as evenly as possible by rows, and a workbook with fewer sheets gives one part per sheet.
  Each part is a copy of the workbook with only its sheets, keeping their formats, widths and
  formulas. "Every N pages" and "about N words" leave it out with a reason (cut by sheets).
- [x] **AC-04** The parts keep their format (`.txt`, `.csv`, `.xlsx`). With "Their Markdown"
  or "Both", each part's Markdown is also written, converted as Convert would.
- [x] **AC-05** The three windows and the command line take these files in Split. The texts
  (start screen, step 1, reasons) name the new formats, in English and Spanish.
