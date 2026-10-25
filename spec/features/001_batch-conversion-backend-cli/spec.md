# Feature 001 — Batch conversion: backend + CLI

## Goal

A user points ClearMD at files and/or folders and gets Markdown files in a `ClearMD_Output` folder, plus a
summary that explains what happened — from the command line, on a backend that every GUI will reuse unchanged.

## Scope

- **Includes:**
  - The batch pipeline of ADR-0010: inputs → scan → detect → **plan** → confirm → **execute** → summary.
  - Formats through the markitdown adapter (ADR-0004): PDF, docx, pptx, xlsx, HTML (full page), CSV, EPUB,
    Jupyter notebooks (`.ipynb`) and plain text (`.txt`).
  - Format detection by extension, and by content (`magika`) when the extension is missing or unknown.
  - Conversions in a **worker process** with time, memory and archive limits, processed from the cheapest to
    the most expensive file (ADR-0015).
  - The output layout and the `Resumen_ClearMD.md` summary with its history (ADR-0016).
  - Progress events and error codes for future interfaces (ADR-0013).
  - English and Spanish for every message and for the summary; English by default (ADR-0012, ADR-0017).
  - Reading the shared settings file (ADR-0012). The CLI never writes it.
  - The complete CLI.
  - A **benchmark** that measures time and memory per format and size, and sets the limits and cost weights.
- **Does not include:** `.tex`, `.odt` and HTML article mode (features 002–004); presenter, GUIs, settings
  window and the remembered output folder (005+); executables and CI (006); ZIP archives, OCR and image
  extraction (out of scope); a second queue lane or parallel workers (deferred, ADR-0015).

## Definitions

- **Input:** a path the user passes (file or folder).
- **Output parent:** the folder that contains the input file, or the parent of the input folder. For an input
  folder that is the root of a drive or the user's home, the folder itself. `--output-root DIR` replaces it.
- **Output root:** `<output parent>/ClearMD_Output`. It holds `Resumen_ClearMD.md` and `Output/`.
- **Batch:** all inputs of one invocation.
- **Plan:** every planned conversion and every skipped item, computed **before writing anything**.
- **ZIP-based document:** docx, pptx, xlsx and epub (and odt from feature 003).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_001_*.py`).

### Inputs and scanning

- [ ] **AC-01** Given a supported file `D/report.pdf`, when it is converted, then
  `D/ClearMD_Output/Output/report.md` exists, is UTF-8 with LF line endings, and contains the document's text.
- [ ] **AC-02** Given a folder `P/project/` with nested subfolders, when it is converted, then
  `P/ClearMD_Output/Output/project/` mirrors its structure for every supported file, and no empty folder is
  created for subfolders without supported files.
- [ ] **AC-03** Given `--no-recursive` (or the setting `recursive = false`), only the files directly inside an
  input folder are converted.
- [ ] **AC-04** Given several inputs from different places, each result goes to the output root of its own
  input.
- [ ] **AC-05** Scanning never enters a folder named `ClearMD_Output` (any letter case), never follows
  symbolic links, and skips hidden files and folders (name starting with `.`, or the hidden attribute on
  Windows) and Office lock files (`~$*`). A skipped folder is reported once, not file by file.
- [ ] **AC-06** Given an input that does not exist, it is reported and the rest of the batch continues. Given
  inputs with nothing to convert (e.g. an empty folder), the CLI says so, exits with 0 and creates no
  `ClearMD_Output`.
- [ ] **AC-07** A file larger than 250 MiB is skipped with the reason "too large".
- [ ] **AC-08** `.md` / `.markdown` files are skipped as "already Markdown"; `.zip` files are skipped with
  "ZIP archives are not supported — extract them first".
- [ ] **AC-09** A ZIP-based document whose contents would expand to more than 1 GiB, or with a compression
  ratio above 100:1, is skipped as "this file looks damaged or unsafe". It is checked from the archive's index,
  without decompressing anything.

### Detection

- [ ] **AC-10** Given a supported document without extension, or with an unknown one, it is detected by its
  content and converted; the summary says "detected by content".
- [ ] **AC-11** Given an unsupported file, it is skipped as "unsupported format" and the batch continues.

### Output location and names

- [ ] **AC-12** Given an input folder that is the root of a drive or the user's home, `ClearMD_Output` is
  created inside it and its contents go directly into `Output/`.
- [ ] **AC-13** `--output-root DIR` writes to `DIR/ClearMD_Output/` with the same layout (`Output/name.md` for
  files, `Output/<folder>/…` for folders).
- [ ] **AC-14** Outputs of one batch that would collide — compared **case-insensitively** — all get the source
  extension: `report.pdf` and `Report.docx` → `report (pdf).md` and `Report (docx).md`. If they still collide,
  a counter follows in path order: `report (pdf).md`, `report (pdf 2).md`. A source without extension uses
  its detected format. No output of a batch overwrites another, and the names do not depend on input order.
- [ ] **AC-15** The output keeps the full source stem: `report.v2.final.pdf` → `report.v2.final.md`; Unicode
  names (`informe_año_ñ.docx`) are preserved.

### Existing outputs

- [ ] **AC-16** Given outputs that already exist from a previous run, the plan marks them, and in an
  interactive terminal the CLI asks **once**: overwrite all, skip all, or decide one by one.
- [ ] **AC-17** `--overwrite` and `--skip` answer that question in advance; using both is a usage error.
- [ ] **AC-18** Given existing outputs, no interactive terminal, no flag and the setting
  `on_existing_output = "ask"`, nothing is written, the exit code is 3 and the message names the flags to use.
  If the setting is `overwrite` or `skip`, it is applied without asking.

### Execution and the worker process

- [ ] **AC-19** Conversions and content detection run in a separate worker process: after a batch, the CLI
  process has not imported `markitdown` nor `magika`.
- [ ] **AC-20** Files are converted from the lowest to the highest estimated cost (size — uncompressed for
  ZIP-based documents — times a per-format weight), ties broken by path. The order is the same for any input
  order.
- [ ] **AC-21** A file that fails to convert does not stop the batch; the summary lists it with a human message
  and the technical detail; the exit code is 1.
- [ ] **AC-22** A password-protected PDF fails with the code `password_protected` and the message "This PDF is
  password-protected. Remove the password and try again."; a corrupt file fails with `corrupt_file`.
- [ ] **AC-23** A file that exceeds the time limit fails with `timed_out`; the worker is replaced and the
  batch continues.
- [ ] **AC-24** A worker that exceeds the memory limit is stopped; the file fails with `out_of_memory` and the
  batch continues with a new worker.
- [ ] **AC-25** If the worker dies (e.g. a crash in native code), the file fails with `worker_crashed` and the
  batch continues with a new worker.
- [ ] **AC-26** Cancelling (Ctrl+C) stops the current file **at once** by stopping the worker. No partial `.md`
  is left; files finished before remain, the rest are reported as cancelled, the summary is still written, and
  the exit code is 130.
- [ ] **AC-27** If an output root cannot be written (permission denied), its files fail with
  `permission_denied` and the suggestion to choose another folder (`--output-root`); other output roots
  continue.

### Summary

- [ ] **AC-28** Each output root gets `Resumen_ClearMD.md` (that name in every language), in the user's
  language. On top, the last batch: date, ClearMD version and totals; a **name table** mapping each source to
  its output, with the detected format and how it was detected; skipped items (reason); failed items (human
  message + technical detail); cancelled items.
- [ ] **AC-29** At the bottom, a **history**: one line per earlier batch in that output root, newest first
  (date and totals), carried over from the previous summary. If the previous history cannot be read, it starts
  again and the summary says so.
- [ ] **AC-30** The CLI ends with a summary: converted / skipped / failed counts and the output folder(s).

### Language and settings

- [ ] **AC-31** Every CLI message and the summary are in English or Spanish. Resolution order: `--lang` →
  settings → English. argparse's own usage and error messages stay in English (ADR-0017).
- [ ] **AC-32** Every catalog key exists in both languages, with the same placeholders.
- [ ] **AC-33** A missing settings file means defaults. An unreadable or invalid one means defaults for the
  invalid values plus a one-line warning — never a crash.
- [ ] **AC-34** CLI flags override settings for that run only.

### CLI contract

- [ ] **AC-35** Exit codes: `0` every planned conversion succeeded (skips are not failures) · `1` at least one
  conversion failed · `2` usage error or no valid input · `3` a decision is required but there is no
  interactive terminal · `130` cancelled. If a batch is cancelled after some failures, 130 wins.
- [ ] **AC-36** `--open` opens the output folder(s) in the system file browser when the batch ends. The CLI
  never does it by default.
- [ ] **AC-37** `--dry-run` shows the plan (including skips and existing outputs) and writes nothing.
- [ ] **AC-38** Progress is shown per file (`[3/37] report.pdf`) on standard error; `--quiet` shows only the
  summary and errors.

### Privacy

- [ ] **AC-39** No conversion opens a network connection (ADR-0005): the test suite makes any socket
  connection fail, and markitdown plugins are disabled.

## Actors and data

- **Actors:** a user through the CLI. Feature 005 adds the presenter and the GUIs on the same backend.
- **Data:** user documents (read-only), the generated `.md` files and `Resumen_ClearMD.md` (inside
  `ClearMD_Output` only), the settings file (read-only in this feature). Nothing is stored anywhere else; nothing
  leaves the machine.

## Risks / open questions

- **markitdown's error details are internal:** mapping exceptions to `password_protected` / `corrupt_file`
  depends on what its converters raise. Verified with fixtures; anything unknown falls back to
  `conversion_failed`.
- **Worker start-up cost:** Python + markitdown + the magika model are loaded once per batch (and after every
  replacement). The benchmark measures it.
- **Two magika models in the worker:** `MarkItDown()` always creates its own `Magika()` and does not accept one;
  the content detector needs one too. The benchmark measures the memory of the second instance and decides
  between keeping it or reusing markitdown's (a private attribute, acceptable only because the version is
  pinned and a test guards it).
- **Limit values:** the initial values of ADR-0015 are replaced by the benchmark's results.
- **argparse in English:** a known gap (ADR-0017).
- **Windows specifics** (hidden attribute, long paths, case-insensitive file system, spawn start method) are
  tested on Linux by simulation here and on a real Windows machine and runner in feature 006.
- **Conversion quality** (PDF tables, layout) comes from markitdown and pdfminer, not from ClearMD.
