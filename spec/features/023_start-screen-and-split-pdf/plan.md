# Plan — Feature 023: Start screen and Split PDF

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0043, ADR-0044.

- **Schemas:**
  - `schemas/split.py`: `Cut`, `Keep`, `SplitSpec`;
  - `PlannedConversion.split`, `ConversionOutcome.parts`, `SkipReason.NOT_SPLITTABLE`,
    `SPLIT_DIR_NAME`;
  - settings `split_cut`, `split_parts`, `split_pages`, `split_keep`, with `RANGES` for whole
    numbers.
- **Worker:**
  - `services/split/pdf_pages.py`: count and cut with PDFium;
  - `worker/pages.py` and `protocol.py`: `CountPagesRequest`, `CutRequest`;
  - `WorkerRunner.count_pages` and `.cut`, behind the `PageCutter` port.
- **Use cases:**
  - `splitting.py`: `page_ranges`, part names, `split_one`, the merged notes;
  - planning: the Split mode and `split_target_for`;
  - execution: a split item goes to `split_one`;
  - `output_files`: `OutputSep` prepared and swept.
- **Api:**
  - `plan_batch(split=…)`; `run_batch` names the parts in the user's language;
  - the summaries move to `api/summaries.py`.
- **Summary:** a Split batch says "split", `OutputSep/`, and "name/ (N parts)".
- **Command line:** `--split-parts`, `--split-pages`, `--keep`.
- **Catalogs:**
  - `[gui.home]`, `[gui.split]`, `[tool.split]` (Split's words for Convert's keys);
  - `Catalog.for_tool`;
  - the Split settings.
- **Presenter:**
  - `Tool`, `HOME` (page 0, where the window opens);
  - `intents/tools.py`: `choose_tool`, `go_home`, `choose_split`;
  - `OutputChoice` carries Split's choices;
  - the review says how each file will be cut.
- **The three windows:** `views/home.py` (two tiles and the note), Home in the rail, Split's block
  on step 1 in place of the images, Split in Settings, screenshots.
