# Plan — Feature 040

- AC-01: `ErrorCode.EMPTY_RESULT`; `worker/child.handle` fails a result without text.
- AC-02: `scan_rules.natural_key`.
- AC-03: `gui.app.details_copied` with `{report}`; a test forbids "/issues" in the catalogs.
- AC-04: `markdown_out/safe_output` (`_pictures`, `_DEFINITION`, attribute tags, entities decoded);
  `worker/pages` (Merge's read text, Markdown parts); `escaping.escape_text` readable marks;
  `tests/support/markdown_guarantee.live_syntax` as the oracle.
- AC-05, AC-11 (focus): the windows (agents).
- AC-06: `output_files.sweep_temporary_files` (`STALE_SECONDS`); `PartStage.drop` and a missing
  part fails `commit`.
- AC-07: `pdf/pdfium/hidden._invisible_without_scan`; ADR-0054 amended.
- AC-08: `tex/source` (UTF-16 BOM, `SHORT_ALLOWANCE`); `use_cases/footnotes.own_footnotes`;
  `split/text_cut.csv_rows` (RFC 4180).
- AC-09: `cleaner/items.ORDERED`, `Flow.marker`; `cleaner/running` short documents; ADR-0030.
- AC-10: `intents/conversion` (kept count), `screens/review.skipped_tone`, `summary/content`
  (`FELL_BACK`), `intents/reset.shown_result`, `skip_action.too_large`.
- AC-11 (board): `NoteKind.HTML_FULL_PAGE`; ADR-0023, ADR-0025, ADR-0044 amended; ADR-0055.
