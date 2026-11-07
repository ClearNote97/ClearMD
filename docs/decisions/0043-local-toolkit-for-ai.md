# ADR-0043: ClearMD becomes a local toolkit that prepares documents for AI: Convert, Split, Merge

- **Status:** accepted
- **Date:** 2026-11-07
- **Amends:** `00_purpose` (mission), `02_scope` (in and out of scope).
- **Supersedes:** in ADR-0019, the single "Tools" window with two tabs. The output folders stay.

## Context

ADR-0019 planned Merge and Split as a secondary "Tools" window, added on to a Markdown converter.
On 2026-11-07, after v1.2.0, the owner reframed the product as a local "iLovePDF" aimed at
Markdown and AI. That means three tools of the same rank. Some people will only split a PDF and
keep the PDF parts. Others will only merge.

Two facts support this:

- An AI chat cannot take an 800-page document. Someone has to cut it into parts that fit, and today
  that means a web service that uploads the file.
- PDFium, through pypdfium2, already reads PDFs for ClearMD (ADR-0030). It can also copy pages into
  a new PDF, so no new dependency is needed.

ClearMD has no telemetry and will never have any (ADR-0005). What people use is learned openly,
from GitHub issues and discussions.

## Decision

- **Identity.** ClearMD is a **local toolkit that prepares documents for AI**, with three tools of
  the same rank:
  - **Convert:** documents to Markdown, as in v1.
  - **Split:** one large file into parts.
  - **Merge:** several files into one.

  Every tool runs 100 % on the computer.
- **Files, never content.** The tools change **files**: they cut a file into parts, join files
  into one, or convert a file's format. They never rewrite, summarise or edit the text inside.
  Each part keeps its pages or rows whole, in order. Every window says in plain words what a tool
  will do before it does it.
- **The user chooses.** Split asks how to cut:
  - into a number of parts;
  - every N pages or rows;
  - into parts that fit an AI's context.

  The context size is an estimate from the text, shown as approximate. No tokenizer is downloaded.

  Each tool also asks what to keep: the parts or the merged file in their own format, in Markdown,
  or both.
- **One start screen.** Three large tiles, Convert, Split and Merge, in the style of feature 021's
  tiles. Each tool follows the same three steps (Choose → Review → Results) in the three
  windows. The command line gets `--split-parts`, `--split-pages` and (with Merge) `--merge`. A tile appears only with its
  tool: the screen starts with Convert and Split, and Merge's tile comes with Merge. In Convert,
  a file that is too big offers **"Split It"**, which opens Split with a recommended cut.
- **Output folders** (ADR-0019, unchanged): `OutputMD/` (Markdown), `OutputSep/` (parts),
  `OutputUnif/` (merged files), all inside `ClearMD_Output/`. Every tool writes into
  `Resumen_ClearMD`.
- **Formats.** Split starts with PDF (by pages), then plain text, CSV, Excel (by rows or sheets)
  and Markdown (by headings). Merge takes Markdown, and also PDFs into one PDF. Mixed documents are
  merged by converting them and joining the Markdown.

## Consequences

- **Gains:**
  - a clearer reason to use ClearMD (documents ready for AI, without uploading them);
  - Split also fixes the files Convert marks as too big today;
  - all of it reuses the core, the worker's limits and the three steps.
- **Costs:**
  - each tool is built in the presenter, the three windows and the command line;
  - the start screen changes the first step every user sees;
  - ClearMD now writes PDFs (only by copying pages), so the "Markdown only" line of `02_scope` is
    widened, and the new wording is precise about it.
- **Version:** the start screen with Split is version **2.0.0**.

## Alternatives considered

- **Keep the "Tools" window of ADR-0019.** Rejected: it hides the tools behind conversion, while
  some people come only to split or merge.
- **Split and merge only on the way to Markdown, never keeping PDF parts.** Rejected by the owner:
  the user chooses what to keep.
- **Count tokens exactly with a model's tokenizer.** Rejected: it means downloading or bundling a
  tokenizer, and the size differs from one AI to another. An honest estimate is enough to choose a
  cut.
