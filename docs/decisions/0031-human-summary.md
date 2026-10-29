# ADR-0031: A summary in human language, and its PDF

- **Status:** accepted
- **Date:** 2026-10-29
- **Refines:** ADR-0016 (Resumen_ClearMD.md, one per output folder) and ADR-0022 (notes).

## Context

The author found the summary of v0.1.0 useful but technical. It read as a log: counters, long
relative paths, sections in a fixed order whatever happened. The author asked for:
- a summary that says first how it went and what to do;
- names instead of long paths;
- where the files are;
- the history folded away;
- a PDF of it in the app's look, for people who will not open a `.md`.

## Decision

- **The Markdown summary is written for a person, in this order:**
  - a headline: ✅ when everything was converted, ⚠️ when something needs attention, ❌ when
    nothing was converted, ⏹️ when the batch was cancelled. One sentence says how many of how
    many, and how many things need attention;
  - the line of the batch (date · version · totals), as before: the history is made of it;
  - **Where your files are:** the Markdown folder, in one sentence;
  - **Needs your attention:** what failed, was stopped, or converted with notes. Each with its
    mark, its name, its folder apart, what happened and what to do;
  - **Converted:** a table of document, folder, result and time;
  - **Left out, Kept, Cancelled** (as before, with names);
  - the **history**, folded in a `<details>` block. Its markers and its 200 lines stay; only lines
    ClearMD wrote are carried over (ADR-0016).
- **Names, not paths.** A file is shown by its name. Its folder, relative to where the batch
  started, is shown apart, and only when it is not the top folder. Every name stays a code span
  that a hostile name cannot close (ADR-0023).
- **The PDF report** (`Resumen_ClearMD.pdf`) is written next to the Markdown when the user
  chooses "Markdown + PDF".
  - It holds the same content, in the app's look: the teal band, the status marks drawn as
    coloured circles, the table.
  - Its text is real and selectable. It has no links and no actions.
  - It is written with PDFium (already bundled, ADR-0030), with DejaVu Sans embedded (its license
    ships with it).
  - If it cannot be written, the Markdown still is, and the batch says the summary was not written
    there.
- **The format is a setting**, `summary_format` = `markdown` (default) or `markdown_pdf`:
  - chosen on step 1, under the output ("Summary: Markdown · Markdown + PDF"), and remembered;
  - in Settings too;
  - on the command line: `--summary-pdf`.

## Consequences

- The summary answers "did it work, and what do I do?" in its first lines.
- The PDF adds about 400 KB per output folder (the embedded font) and two font files to the
  executable (about 1.4 MB).
- The summary's tests change. Its guarantees (escaping, history, the planted-link checks) stay,
  with their tests.
