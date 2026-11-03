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

## Next

- [ ] **006b — Hardening of the executables:** **code signing** of the Windows executables
      (SignPath, free for open source — once the repository is public) so SmartScreen does not
      scare non-technical users; a Windows Job Object as the worker's hard memory cap; an advisory
      check of `uv.lock` and hash-pinned builds; executable size as a metric.

## Later

- [ ] **015 — PySide6-Essentials GUI** (*onedir* distribution because of LGPL, ADR-0003).
- [ ] **016 — flet GUI.**
- [ ] A small Windows installer (a Start menu shortcut), optional.
- [ ] Incremental mode: skip files unchanged since the last run.
- [ ] Minor formats: `.eml`, `.rtf`, subtitles.
- [ ] A second queue lane for heavy files, or parallel workers — only if the benchmark shows blocking
      (ADR-0015).
- [ ] **Publish on PyPI** (`pip install clearmd` / `uv tool install clearmd`), at the end (ADR-0018).

## Version 2

- [ ] **Tools window — Merge | Split** (ADR-0019):
      **Merge** `.md` files into one (`OutputUnif/`; the last batch by default, or any `.md` the user picks);
      **Split** a large source document into N similar parts in its own format (`OutputSep/`; PDF by pages
      first, then csv/txt and xlsx).
      From the plan review, a file marked too big or too slow (AC-42/43 of feature 001) offers **"Split it"**:
      Tools opens with a recommended number of parts (from the estimates, so each part fits the limits), and
      the parts replace the file in the batch when the user comes back.

## Out for now

See `spec/constitution/02_scope.md` → Out of scope: network/cloud, OCR, ZIP, image extraction, reverse
conversion, database, macOS.
