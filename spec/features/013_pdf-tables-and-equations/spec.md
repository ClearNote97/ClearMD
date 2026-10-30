# Feature 013 — PDF tables and equations

## Goal

A PDF's tables as Markdown tables, its numbered equations whole, its table of contents one entry
per line (ADR-0034).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_013_pdf_tables_and_equations.py`).

- [x] **AC-01** A table without rules (aligned columns) becomes a Markdown table; prose with wide
  gaps and an aligned formula do not.
- [x] **AC-02** A ruled table becomes a Markdown table, a cell wrapped over lines one cell.
- [x] **AC-03** A table set sideways is read upright; the page's header does not leak into it.
- [x] **AC-04** A numbered equation is one block that keeps its rows; with the images folder, a
  picture cropped from the page.
- [x] **AC-05** A caption starts its own block; a table of contents has one entry per line.
- [x] **AC-06** Camelot is credited, not a dependency; the examples of the author read better
  (evaluated locally, never committed).
