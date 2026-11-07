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
  - It is written with PDFium (already bundled, ADR-0030) in Helvetica, a PDF standard font every
    reader has, so nothing is embedded and the file weighs a few KB. It draws the Windows Latin
    characters (all of English and Spanish). Any other character in a name is drawn as "?"; the
    Markdown keeps the name whole. Embedding a font would add about 400 KB to every summary.
  - If it cannot be written, the Markdown still is, and the batch says the summary was not written
    there.
- **The format is a setting**, `summary_format` = `markdown` (default) or `markdown_pdf`:
  - chosen on step 1, under the output ("Summary: Markdown · Markdown + PDF"), and remembered;
  - in Settings too;
  - on the command line: `--summary-pdf`.

### After review (code review, security audit and adversarial check of 009)

- The headline's mark:
  - ✅ when everything tried was converted. Files only left out (hidden, already Markdown,
    unsupported) are listed, not a failure.
  - ⚠️ when nothing was tried and something was left out.
- A file's folder is its result's, inside `OutputMD`, whatever the output choice. A file left
  out is placed the same way, so no absolute path is ever shown.
- Singular and plural come from the catalog (`.one`, `.other`), in the summary, the command line
  and the window. Counts carry the language's thousands mark, and the history still recognises
  them.
- The PDF:
  - Widths are each character's advance, measured once per font (at most 256), so words are
    spaced by the font.
  - Text from the user's files is capped (names 200 characters, details 500), its middle left out.
  - The table's header comes again on every page.
- An older `Resumen_ClearMD.pdf` is removed whenever the PDF is not written again, only if it is
  a regular file.

## Consequences

- The summary answers "did it work, and what do I do?" in its first lines.
- The PDF adds a few KB per output folder and nothing to the executable.
- The summary's tests change. Its guarantees (escaping, history, the planted-link checks) stay,
  with their tests.

## Amendment (feature 020, v1.1.0, 2026-11-07)

A third format, **PDF only** (`summary_format = "pdf"`, `--summary-pdf-only`): the output folder gets
`Resumen_ClearMD.pdf` and no Markdown summary; an earlier Markdown one is removed. If the PDF cannot be
written, the Markdown summary is written instead (a batch always leaves a summary). The history of
earlier batches lives in the Markdown summary: with the PDF alone it starts again.
