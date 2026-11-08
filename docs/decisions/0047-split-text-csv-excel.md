# ADR-0047: Split cuts text and CSV between lines or rows, and Excel by whole sheets

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0044, ADR-0045.

## Context

After PDF and Markdown, the roadmap asked Split to take text, CSV and Excel. Each part must stay
a valid file of its format, and nothing inside it may change.

## Decision

- **Text** is cut at line breaks: into N parts balanced by words, or parts of about N words.
  The parts, put back together, are the file.
- **CSV** is cut between rows. Rows are found by their quotes, so a quoted field that spans
  lines stays whole. Every part starts with the header row, so each one is a table with its
  column names. That is the only line repeated.
- **Excel** is cut by **whole sheets**: "into N parts" groups the sheets in order, balanced by
  rows. Each part is the workbook loaded and saved with only its sheets (openpyxl), so formats,
  widths, merged cells and formulas stay as they were. A formula that points at a sheet in
  another part loses its target: that is the price of keeping every sheet whole. Excel is never
  cut by rows, because that would break formulas inside a sheet.
- **Cuts that do not apply leave the file out with a reason:** "every N pages" for text and CSV
  (`no_pages_to_cut`); anything but "into N parts" for Excel (`cut_by_sheets`).
- All cutting runs in the worker. The interface process writes the parts, and also each part's
  Markdown when Keep asks for it.

## Alternatives considered

- **Excel by rows:** it breaks formulas and charts that reach across rows.
- **CSV without the header in every part:** the parts would be tables without column names, of
  little use to an AI.
