# ADR-0010: Batch conversion, format autodetection and the `ClearMD_Output` folder

- **Status:** accepted (the fine-grained rules are set in the spec of feature 001)
- **Date:** 2026-10-24

## Context

The real use case is not "one file" but "these files" or "this folder". The user needs to know
**where the result ended up** without choosing a location every time, and the app cannot trust a file's
extension to tell the truth.

## Decision

### Input

- One or more files and/or folders. Folders are walked **recursively** by default
  (`--no-recursive` in the CLI to disable it).
- In the GUIs, two separate actions ("Add files" and "Add folder"), because the native dialogs of
  Windows, Linux and macOS do not allow choosing files and folders in the same window. Drag and drop where the
  toolkit supports it.

### Autodetection

A `FormatDetector` port with chained detectors, from cheapest to most expensive:

1. file extension;
2. internal signature (for example, the `mimetype` file inside the zip of an `.odt`);
3. `magika` (already included with markitdown), which detects the type by content;
4. a heuristic for `.tex` (`\documentclass`, `\begin{document}`), which has no binary signature.

Anything not recognized is skipped and reported; it does not stop the batch.

### Output

- File `D/report.pdf` → `D/ClearMD_Output/report.md`.
- Folder `P/project/` → `P/ClearMD_Output/project/…`, with the same subfolder structure.
- If two inputs **in the same batch** produce the same name, both get a suffix:
  `report (pdf).md`, `report (docx).md`. All destinations are computed before writing, so that the
  result does not depend on the processing order.
- If an output already exists **from a previous run**, the user is asked. **plan → confirm → execute** pattern:
  the core builds the batch plan (destinations, conflicts, skipped files), the GUI shows it and the user decides
  once (overwrite all, skip all, or case by case). In the CLI: `--overwrite` or `--skip`. With no interactive
  terminal and no flag, the CLI exits with an error: **it never overwrites silently**.

### Safety and robustness rules

- Any `ClearMD_Output` folder is excluded from scanning, so results are not reconverted.
- Symbolic links are not followed; hidden files are ignored; there is a per-file size limit.
- Without write permission next to the input: the user is warned and offered another location.
- A file that fails does not stop the batch; each batch leaves a **report** in `ClearMD_Output`.

## Consequences

- **Gains:** the result appears next to the original; computing destinations is a pure function that is easy to
  test; the up-front plan serves as a preview and prevents accidental overwrites.
- **Costs:** more logic in the core (planning, collisions, report) than a file-by-file
  conversion.
