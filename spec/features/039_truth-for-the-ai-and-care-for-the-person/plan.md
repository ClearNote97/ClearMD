# Plan — Feature 039

- AC-01: `tex/source._as_western` tries cp1252 first, kept only when every non-ASCII character is
  Western and most letters are ASCII; `note.encoding_guessed` with its action.
- AC-02: `markdown_out/safe_output.safe_output`, applied in `worker/child.handle` to every
  converter's result (`NoteKind.MADE_SAFE`); `eml._body` with `html.page` and `html.render` in
  memory; `services/privacy.without_paths` (moved from the presenter) in `summary/content`.
- AC-03: `installer/clearmd.iss` and `look/painted.iss` texts, `[Run]` and `FinishedLabel`;
  `RELEASE_NOTES.md` "What to Download"; `packaging/release_notes.py` in `release.yml`; READMEs.
- AC-04: `presenter.choose_language`; `gui.help.ai`, `gui.help.where`; `ResultView.with_ai`.
- AC-05: `planning` warns no PDF; `screens/convert._fraction`; `tools.split_large`/`_give_back`.
- AC-06: `split_notes.part_markdown`/`not_converted`; `split_names.parts_in`/`has_result`;
  `splitting._remove_if_empty`; ADR-0044 amended.
- AC-07: `screens/review` (one count, words, singular), `screens/results` (`INFORMING`),
  `intents/reset` (`stopped_by_error`), `intents/conversion` (opens only when FINISHED).
- AC-08: `pdf/pdfium/hidden.hide_unseen` (ADR-0054), `Document.hidden_pages`/`equation_pages`;
  `markitdown_adapter.merged_cells`; `merging._piece` notes and `[^dN-…]`; `splitting._pdf`.
- AC-09, AC-10: the windows (agents); `intents/inputs.undo_clear`, `View.show_undo`,
  `reset.editable` back to step 1 with `session.notice`; `spec/contracts/ux.md` §6.
- AC-11: `Settings.html_strategy = "article"`; `report.how`; Discussions on; `release.yml` signs
  the installers; ADR-0054 and amendments to 0025, 0036, 0037, 0044, 0053.
