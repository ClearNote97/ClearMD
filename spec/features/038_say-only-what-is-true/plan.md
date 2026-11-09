# Plan — Feature 038

- AC-01: `markitdown_adapter` decodes TXT and CSV with `tex.source.decode_source` (UTF-8, then the
  Western European preference on a tie) and passes UTF-8 to markitdown; `csv_dialect.with_commas`
  works on text; `ENCODING_GUESSED` in plain words.
- AC-02: `presenter/screens/details.without_paths` (quoted names, chosen names, paths to the end of
  their quote or line); `[report] how` filled by `Catalog.text` wherever `{report}` appears.
- AC-03: `text_cut.balanced_cuts` cuts the remaining boundaries when needed; `markdown_cut._into`
  uses blocks when a section is more than twice its share; `NoteKind.PARTS_FEWER`.
- AC-04: `merging._write` catches `Cancelled`; `reset.unexpected` keeps the plan's folders in
  `BatchReport.folders` and shows Results.
- AC-05: `tables/build.joined_continuations`; `blocks/equation_latex.incoherent`.
- AC-06: the windows (agents), from `gui.close.*`.
- AC-07: `rejections.error_action/error_text/skip_action` (`*_other` keys); `EMPTY_FILE` in the
  worker; `chrome/header` by state; catalog pass; `cli/flow` exit 2.
- AC-08: `formats.IMAGE_SUFFIXES`, `PART_NAMES`; `split_names`, `output_files.other_image_folders`;
  `api.run_batch` images for Convert only.
- AC-09: lazy imports in `worker/supervisor` and `api/composition`; `tests/conftest.py`;
  `ci.yml`; `clearmd.spec` COLLECT, `clearmd.iss`, `check_executables.sh`, ADR-0053.
- AC-10: `schemas/limits.py` PDF 4 s/MiB and 6 MiB/MiB.
