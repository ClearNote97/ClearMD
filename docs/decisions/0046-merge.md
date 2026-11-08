# ADR-0046: Merge joins documents into one Markdown or one PDF, in the list's order

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0043 (the toolkit), ADR-0044 (the worker's page jobs), ADR-0019
  (`OutputUnif/`).

## Context

Merge is the third tool. An AI is easiest to use with one file. Some people also want one PDF
made of several PDFs. As with Split, the tool must change files and never their content.

## Decision

- **A mode of the same batch.** A plan may carry a `MergeSpec`:
  - Planning keeps the list's order, not the cost order: the files of a folder go in name order.
  - Every document shares one output folder, the first document's, and one target,
    `OutputUnif/Merged <date time>.md|pdf`. The name is in the user's language, and the time
    makes it unique.
- **Into one Markdown.** Each document is converted as Convert converts it, with its own time
  limit. A Markdown file is read as it is, in the worker. The texts are joined in order. Each
  starts with `<!-- ClearMD: name -->`, a comment that a Markdown viewer does not show and an AI
  reads. Nothing else is added.
- **Into one PDF.** Only PDFs: any other file is left out with a reason. Each PDF is opened
  first, so a broken or locked one fails alone. Then the worker copies every page, whole and in
  order (`MergePdfRequest`).
- **Failures.** A document that fails is left out and told. With fewer than two documents left,
  nothing is written, and those documents are told why (`nothing_to_merge`).
- **The command line:** `--merge markdown|pdf`, never together with a split. The setting is
  `merge_into`.
- **The words.** The summary and the windows speak as Merge does: `[tool.merge]`, and a summary
  that knows its tool (convert, split, merge).

## Consequences

- **Gains:**
  - the conversions, limits, cancelling and summary are the same code;
  - an AI gets one file, with each document's source still known.
- **Costs:**
  - the merged Markdown is held in memory before it is written (each document's own result
    stays under the result limit);
  - the order is the order in which the files were listed: there is no "move up/down" yet.

## Alternatives considered

- **A visible heading per document:** it would add text to the documents. The comment is
  invisible, and still tells an AI the source.
- **pypdf to merge PDFs:** PDFium already copies pages for Split (ADR-0044).
