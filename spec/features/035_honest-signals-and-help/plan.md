# Plan — Feature 035

- **Notes' levels** (`schemas/notes.py`: `NoteKind.informs`, `INFORMATION`;
  `ConversionOutcome.worth_a_look`): the summary's attention list takes only outcomes worth a
  look; the others go to `SummaryContent.cleaned` (Markdown and PDF). The CLI line follows.
- **Kept** (`presenter/screens/results.py`, `Catalog.totals(kept=)`): not a row; a "Kept" figure;
  `result_folders` counts kept ones; `where_line` writes the folders.
- **Rows** (`ResultRow.tone`, `gui.result.word_*`).
- **Help** (`presenter/screens/help.py`): `help_sections(catalog, drops=)`, rendered by each
  window's Help dialog.
- **Step 3** (`chrome/secondary.ready_line(catalog, plan, setting, answer)`): the windows pass
  Settings' choice and Review's answer.
- **Review's detail line** and **Results' path line**: drawn by each window (the Results pattern).
- **ttk list**: scroll bar packed first; images cached; only changed rows updated.
