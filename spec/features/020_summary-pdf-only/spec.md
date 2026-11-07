# Feature 020 — The summary as a PDF alone

## Goal

Some people only want the PDF summary (to read or print), not the Markdown one beside it. A third
summary format, **PDF only**, writes `Resumen_ClearMD.pdf` and no `Resumen_ClearMD.md`
(ADR-0031, amended).

## Scope

- **Includes:** the setting value `pdf`; the backend writing the PDF alone; the choice on step 1 and
  in Settings of the three windows; `--summary-pdf-only` on the command line; texts in English and
  Spanish.
- **Does not include:** a history of earlier batches in the PDF (the Markdown summary keeps it;
  with the PDF alone it starts again); other formats.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_020_*.py`).

- [x] **AC-01** With PDF only, an output folder gets `Resumen_ClearMD.pdf` and no
  `Resumen_ClearMD.md`.
- [x] **AC-02** An earlier batch's Markdown summary does not stay beside the new PDF (and an
  earlier PDF does not stay beside a new Markdown one, as before).
- [x] **AC-03** If the PDF cannot be written, the Markdown summary is written instead, and it is told:
  a batch never ends without a summary.
- [x] **AC-04** The setting decides; `--summary-pdf-only`, `--summary-pdf` and `--no-summary-pdf`
  override it for one run.
- [x] **AC-05** The presenter asks the backend for the PDF alone when the setting is PDF only.
- [x] **AC-06** The third choice is on step 1 and in Settings of the ttk, Qt and flet windows, and it is
  remembered.
- [x] **AC-07** Its texts in English and Spanish, the command line's help included; version 1.1.0.
