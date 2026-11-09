# Plan — Feature 034

- **Parts written aside** (`use_cases/part_stage.py`): every part goes to a hidden staged name
  (`.<name>.clearmd-part.<ext>`) in its folder; `commit` moves them in and only then removes the
  earlier cut's other parts; `discard` removes the staged ones. The start-up sweep removes
  staged names a power cut leaves.
- **Merge** (`use_cases/merging.py`): `free_target` adds " (2)", " (3)"; a visible heading per
  document from the catalog (`merge.heading`, set with the name in `api/naming.py`); the
  results folder is prepared in every branch, and a cancelled merge is cancelled.
- **Two documents** (`presenter/screens/primary.py`): Merge's Next disabled with one file input,
  and on step 2 when the plan has one conversion.
- **Once per file** (`use_cases/scanning.first_time`, `planning`): the real path, case-folded as
  the system does, decides; the repeat is a `SkipReason.ALREADY_INCLUDED`.
- **CSV** (`services/conversion/csv_dialect.py`): the separator that splits the first 50 lines
  evenly; a non-comma file is rewritten with commas before markitdown reads it.
- **Links** (`use_cases/relink.py`): relative links to existing files rewritten for the new
  folder, in Split's Markdown parts and in every merged piece.
