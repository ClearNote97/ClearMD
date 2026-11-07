# ADR-0044: Split cuts a PDF by whole pages in the worker; Markdown part by part

- **Status:** accepted
- **Date:** 2026-11-07
- **Refines:** ADR-0043 (the toolkit), ADR-0015 (the worker and its limits), ADR-0019 (`OutputSep/`).

## Context

Split is the second tool (feature 023). A PDF must be cut into parts without touching what is inside
them. A huge PDF is exactly the file Convert stops at its time limit, so its Markdown must come part
by part, each within that limit. Reading a document stays in the worker process (ADR-0015). Writing
stays in the interface process, inside `ClearMD_Output` and never through a link (security review of
feature 001).

## Decision

- **Split is a mode of the same batch.** A `PlannedConversion` may carry a `SplitSpec`: the cut
  (into N parts / every N pages), its size, what to keep, and the parts' name in the user's
  language. Planning, the review, the queue, cancelling, the "if it already exists" rule, the
  summary and the history stay the same code. In a Split plan, any file that is not a PDF is left
  out with a reason (`not_splittable`).
- **Two worker jobs.** `CountPagesRequest` returns the page count. `CutRequest(first, last)`
  returns a new PDF with those pages, copied whole by PDFium (`import_pages`, which keeps the fonts
  and images they use). The interface process writes each part atomically
  (`atomic_write_bytes`).
- **The cut** is a pure function of the page count:
  - **Into N parts:** as even as possible, with the first parts a page longer.
  - **Every N pages:** the last part may be shorter.
  - Never more parts than pages, never an empty part.
- **Markdown part by part.** Each part is converted by the usual PDF converter, as its own request,
  so each one has the whole time limit. With "Markdown" alone, each PDF part is removed once its
  Markdown is written. The parts' notes become one note per kind, with the pages counted in the
  whole PDF.
- **Where the parts go:** `ClearMD_Output/OutputSep/<relative folder>/<name>/`, one folder per
  document. Each part is named `<name> - part 01 of 12.pdf|md` (Spanish: `parte 01 de 12`); the
  index is padded so the parts sort right. On overwrite, only the names of an earlier cut of that
  document are removed, never other files.
- **The command line:**
  - `--split-parts N` (N ≥ 2) or `--split-pages N` (N ≥ 1), never both;
  - `--keep pdf|markdown|both`, which defaults to the `split_keep` setting (`both`).
- **Settings:** `split_cut`, `split_parts`, `split_pages` and `split_keep`. Whole numbers are a
  new kind of setting, kept within their bounds.
- **The windows** speak as the tool does. `Catalog.for_tool("split")` overlays Split's words,
  `[tool.split]` in the catalogs, on Convert's keys, so every view keeps its keys.

## Consequences

- **Gains:**
  - little new code in the core;
  - the worker's safety and limits apply to Split as they do to Convert;
  - a too-big PDF can now be turned into Markdown through Split.
- **Costs:**
  - a part's bytes travel through the pipe, within the same result limit as a Markdown result;
  - copying pages can duplicate shared resources, so the parts together may be larger than the
    source.

## Alternatives considered

- **The worker writes the parts itself.** Rejected: writing stays in one place, inside
  `ClearMD_Output`, with the link checks.
- **pypdf.** Rejected: PDFium already reads PDFs for ClearMD, and a second PDF library adds weight
  and another parser.
- **One request per document (cut and convert together).** Rejected: the time limit would apply to
  the whole document, which is the problem Split solves.
