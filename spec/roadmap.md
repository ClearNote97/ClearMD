<!--
====================================================================
 ROADMAP  ·  spec/ (outside the Constitution)
--------------------------------------------------------------------
 Changes often; purpose, principles and stack do not.
 Orders the features (spec/features/NNN_...) in time.
====================================================================
-->

# Roadmap

A walking skeleton with the cheapest interface first: every new GUI reuses a core and a presenter that are
already tested (ADR-0001).

## Now

- [x] **Phase 0:** template pruning, `clearmd` package in the template layout, ADRs 0001–0018, UX contract,
      clean dev container.
- [x] **001 — Batch conversion: backend + CLI** ([spec](./features/001_batch-conversion-backend-cli/spec.md)):
      worker process with limits, cost-ordered queue, detection, plan → confirm → execute,
      `ClearMD_Output/OutputMD/` + `Resumen_ClearMD.md` with history, markitdown adapter, i18n EN/ES, settings
      (read), complete CLI, benchmark.
- [x] **002 — `.tex` converter** ([spec](./features/002_tex-converter/spec.md)): the subset, math preserved,
      includes inside the document folder, the author's macros expanded with limits, honest conversion notes
      (ADR-0022).
- [x] **003 — `.odt` converter** ([spec](./features/003_odt-converter/spec.md)): standard library only, XML
      read safely (pyexpat, DOCTYPE refused, limits), formulas as LaTeX, images as placeholders, the output
      guarantee shared with `.tex`, a growth budget for everything written again (ADR-0024).
- [x] **004 — HTML article mode** ([spec](./features/004_html-article-mode/spec.md)): trafilatura finds the
      article, ClearMD writes it with the shared guarantee (a page with no article too), `--html full|article`
      and the `html_strategy` setting, the strategy in the plan and the summary (ADR-0025).

- [x] **005 — Presenter (MVP) + ttkbootstrap GUI** ([spec](./features/005_presenter-and-ttk-gui/spec.md)):
      the presenter every GUI shares (ADR-0026), the ttk window in ClearMD's own look — the rail
      with the four steps, the C·M↓ logo, file icons, teal light and dark themes (ADR-0027) —
      help, welcome, settings; reviewed (code, security, adversarial verification).
- [x] **006 — CI and executables** ([spec](./features/006_ci-and-executables/spec.md)): tests on Linux and
      Windows (Python 3.12 and 3.14); the desktop app and the command line as one-file executables
      for Windows and Linux, each build checked by a real batch; GitHub (pre-)releases with the
      third-party notices (ADR-0028).

- [x] **007 — Navigation and window polish** ([spec](./features/007_navigation-and-polish/spec.md)):
      free navigation between the four steps, Next / Next / Convert, checkboxes and separators in
      the lists, a smooth resize and a compact rail, the version on screen, a splash with progress. Reviewed (code, security,
      adversarial).

- [x] **008 — PDF quality** ([spec](./features/008_pdf-quality/spec.md), ADR-0030): PDFium for
      the text, ClearMD's own cleaning (repeated headers and page numbers, hyphenation, paragraphs,
      footnotes, headings), glyph codes read back, unreadable text told. Reviewed (code, security,
      adversarial).

- [x] **009 — A summary in human language, and its PDF**
      ([spec](./features/009_human-summary/spec.md), ADR-0031) in the app's look; the format
      chosen on the first screen and in Settings. Reviewed (code, security,
      adversarial).

- [x] **010 — A light executable** ([spec](./features/010_light-executable/spec.md), ADR-0032): own
      detection for files without an extension (no magika), own Excel converter (no pandas),
      babel's data for two languages; about 90 → 40 MB. Reviewed (code, security,
      adversarial).

- [x] **011 — Window polish II** ([spec](./features/011_window-polish-2/spec.md)): Settings and
      Help as sections of the rail, the shape whole above an outlined page, the hint says what is
      missing on every page. Reviewed.

- [x] **012 — Images in a folder:** `<document>_images` (`_imagenes` in Spanish), a setting off
      by default, chosen on step 1 and in Settings. Reviewed.

- [x] **013 — PDF tables and equations:** tables after Camelot's stream and lattice methods on
      PDFium; equations as images when images are kept; the table of contents line by line. Reviewed.

- [x] **014 — Sub- and superscripts, window polish III**
      ([spec](./features/014_scripts-and-window-polish-3/spec.md)): a PDF's scripts as such and its
      equations whole; one gutter; each page's cards faded before there is anything in them. Reviewed.

- [x] **015 — A PDF's equations as LaTeX**
      ([spec](./features/015_equations-as-latex/spec.md)): fractions, sums, brackets, scripts and
      rows rebuilt from the places of their pieces; equations with no number found by their bar.

## Next

- [ ] **006b — Hardening of the executables:** **code signing** of the Windows executables
      (SignPath, free for open source) so SmartScreen does not scare non-technical users — *the
      workflow and the policy are ready (ADR-0037); waiting for SignPath Foundation's approval*;
      a Windows Job Object as the worker's hard memory cap; an advisory check of `uv.lock` and
      hash-pinned builds; executable size as a metric.

## Later

- [x] **016 — PySide6-Essentials GUI** (*onedir* distribution because of LGPL, ADR-0003, ADR-0038): v0.11.0.
- [x] **017 — Windows installer and uninstaller** (Inno Setup, ADR-0040): v0.12.0.
- [x] **018 — flet GUI** (a folder with flet's own window program, ADR-0042): v1.0.0, ClearMD 1.0.
- [x] **019 — The installer looks like ClearMD** (pictures, light and dark, the apps' palette, ADR-0041): v0.13.2.
- [x] **020 — The summary as a PDF alone** (ADR-0031 amended): v1.1.0.
- [x] **021 — flet's empty list as two large tiles; titles in Title Case** (ADR-0042 amended): v1.2.0.
- [x] **022 — The files a public project carries; checksums with every release**: v2.0.0.

## Version 2 — a local toolkit that prepares documents for AI (ADR-0043)

Convert, Split and Merge as three tools of the same rank, on a start screen with three tiles. Each tool
follows Choose → Review → Results in the three windows; the command line gets `clearmd split` and
`clearmd merge`. The tools act on files, never on their content.

- [x] **023 — Start screen and Split PDF** (ADR-0044): v2.0.0: the tiles Convert and Split (Merge's tile arrives with
      026: never a tile without its action); Split cuts a PDF into a number of parts or every N pages,
      and keeps the PDF parts, their Markdown, or both (`OutputSep/`).
- [x] **024 — Split into parts that fit an AI** (ADR-0045): v2.1.0: the cut by estimated context size (approximate,
      no tokenizer downloaded), for PDF and Markdown (Markdown by headings).
- [x] **025 — "Split It" from Convert**: v2.2.0: a file marked too big or too slow (AC-42/43 of feature
      001) offers to split it, with the recommended cut; the parts come back to the batch.
- [x] **026 — Merge** (ADR-0046): v2.3.0: several `.md` into one, PDFs into one PDF, and mixed documents converted
      and joined (`OutputUnif/`); the order chosen by the user.
- [x] **027 — Split more formats** (ADR-0047): v2.4.0: text and CSV by lines (the CSV header in every part), Excel by whole sheets.
- [x] **028 — Incremental mode** (ADR-0048): v2.5.0: "Replace it if the original changed".
- [x] **029 — Minor formats** (ADR-0049): v2.6.0: `.eml`, `.rtf`, `.srt` and `.vtt`.
- [x] **030 — Measure the queue** (ADR-0050): measured, no blocking — one worker in cost order stays.
- [x] **031 — Ready for PyPI** (ADR-0051): v2.7.0: metadata, PyPI's page, the build checked on every tag, Trusted Publishing off until the owner turns it on.
- [x] **032 — Merge's order and "What Next?"**: v2.8.0: move a document up or down in Merge; Results offers to go back Home; the start screen alike in the three windows.
- [x] **033 — "What Next?" as the three tools**: v2.8.1: the three tools as small tiles and one "Keep the files" box.

## Out for now

See `spec/constitution/02_scope.md` → Out of scope: network/cloud, OCR, ZIP, image extraction, reverse
conversion, database, macOS.
