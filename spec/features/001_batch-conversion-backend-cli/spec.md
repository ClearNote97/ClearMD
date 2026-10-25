# Feature 001 — Batch conversion: backend + CLI

## Goal

A user points ClearMD at files and/or folders and gets Markdown files in a `ClearMD_Output` folder, plus a
summary that explains what happened — from the command line, on a backend that every GUI will reuse unchanged.

## Scope

- **Includes:**
  - The batch pipeline of ADR-0010: inputs → scan → detect → **plan** → confirm → **execute** → summary.
  - Formats through the markitdown adapter (ADR-0004): PDF, docx, pptx, xlsx, HTML (full page), CSV, EPUB,
    Jupyter notebooks (`.ipynb`) and plain text (`.txt`).
  - Format detection by extension, and by content (`magika`) when there is no extension.
  - Conversions in a **worker process** with time, memory and archive limits, processed from the cheapest to
    the most expensive file (ADR-0015).
  - The output layout and the `Resumen_ClearMD.md` summary with its history (ADR-0016).
  - Progress events and error codes for future interfaces (ADR-0013).
  - English and Spanish for every message and for the summary; English by default (ADR-0012, ADR-0017).
  - Reading the shared settings file (ADR-0012). The CLI never writes it.
  - The complete CLI.
  - A **benchmark** that measures time and memory per format and size, and sets the limits and cost weights.
  - An **estimate of the time left** while converting, corrected with the speed measured in the batch, and the
    time each file took in the summary.
- **Does not include:** `.tex`, `.odt` and HTML article mode (features 002–004); presenter, GUIs, settings
  window and the remembered output folder (005+); executables and CI (006); ZIP archives, OCR and image
  extraction (out of scope); a second queue lane or parallel workers (deferred, ADR-0015).

## Definitions

- **Input:** a path the user passes (file or folder).
- **Output parent:** the folder that contains the input file, or the parent of the input folder. For an input
  folder that is the root of a drive or the user's home, the folder itself. `--output-root DIR` replaces it.
- **Output root:** `<output parent>/ClearMD_Output`. It holds `Resumen_ClearMD.md` and `OutputMD/`.
- **Batch:** all inputs of one invocation.
- **Plan:** every planned conversion and every skipped item, computed **before writing anything**.
- **ZIP-based document:** docx, pptx, xlsx and epub (and odt from feature 003).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_001_*.py`).

### Inputs and scanning

- [x] **AC-01** Given a supported file `D/report.pdf`, when it is converted, then
  `D/ClearMD_Output/OutputMD/report.md` exists, is UTF-8 with LF line endings, and contains the document's text.
- [x] **AC-02** Given a folder `P/project/` with nested subfolders, when it is converted, then
  `P/ClearMD_Output/OutputMD/project/` mirrors its structure for every supported file, and no empty folder is
  created for subfolders without supported files.
- [x] **AC-03** Given `--no-recursive` (or the setting `recursive = false`), only the files directly inside an
  input folder are converted.
- [x] **AC-04** Given several inputs from different places, each result goes to the output root of its own
  input.
- [x] **AC-05** Scanning never enters a folder named `ClearMD_Output` (any letter case), never follows
  symbolic links, and skips hidden files and folders (name starting with `.`, or the hidden attribute on
  Windows) and Office lock files (`~$*`). A skipped folder is reported once, not file by file.
- [x] **AC-06** Given an input that does not exist, it is reported and the rest of the batch continues. Given
  inputs with nothing to convert (e.g. an empty folder), the CLI says so, exits with 0 and creates no
  `ClearMD_Output`.
- [x] **AC-07** A file larger than 250 MiB is skipped with the reason "too large".
- [x] **AC-08** `.md` / `.markdown` files are skipped as "already Markdown"; `.zip` files are skipped with
  "ZIP archives are not supported — extract them first".
- [x] **AC-09** A ZIP-based document whose contents would expand to more than 1 GiB, or whose uncompressed
  total is more than 100 times its file size, is skipped as "this file looks damaged or unsafe". It is checked
  from the archive's index, without decompressing anything. (Real documents measured 1–5:1; single entries can
  reach 43:1, so the rule never applies per entry.)

### Detection

- [x] **AC-10** Given a supported document **without extension** (`scan`, `README`), it is detected by its
  content and converted; the summary says "detected by content". A file with an extension ClearMD does not know
  (`report.dat`, `paper.tex` until feature 002) is "unsupported format" without looking inside: what is not
  contemplated is not accepted.
- [x] **AC-11** Given an unsupported file, it is skipped as "unsupported format" and the batch continues.

### Output location and names

- [x] **AC-12** Given an input folder that is the root of a drive or the user's home, `ClearMD_Output` is
  created inside it and its contents go directly into `OutputMD/`.
- [x] **AC-13** `--output-root DIR` writes to `DIR/ClearMD_Output/` with the same layout (`OutputMD/name.md` for
  files, `OutputMD/<folder>/…` for folders).
- [x] **AC-14** Outputs of one batch that would collide — compared **case-insensitively** — all get the source
  extension: `report.pdf` and `Report.docx` → `report (pdf).md` and `Report (docx).md`. If they still collide,
  a counter follows in path order: `report (pdf).md`, `report (pdf 2).md`. A source without extension uses
  its detected format. No output of a batch overwrites another, and the names do not depend on input order.
- [x] **AC-15** The output keeps the full source stem: `report.v2.final.pdf` → `report.v2.final.md`; Unicode
  names (`informe_año_ñ.docx`) are preserved.

### Existing outputs

- [x] **AC-16** Given outputs that already exist from a previous run, the plan marks them, and in an
  interactive terminal the CLI asks **once**: overwrite all, skip all, or decide one by one.
- [x] **AC-17** `--overwrite` and `--skip` answer that question in advance; using both is a usage error.
- [x] **AC-18** Given existing outputs, no interactive terminal, no flag and the setting
  `on_existing_output = "ask"`, nothing is written, the exit code is 3 and the message names the flags to use.
  If the setting is `overwrite` or `skip`, it is applied without asking.

### Execution and the worker process

- [x] **AC-19** Conversions and content detection run in a separate worker process: after a batch, the CLI
  process has not imported `markitdown` nor `magika`.
- [x] **AC-20** Files are converted from the lowest to the highest estimated cost — the estimated conversion
  time: size × the format's seconds per MiB measured by the benchmark, where the size of a ZIP-based document is
  its uncompressed text parts (not its images) — ties broken by path. The order is the same for any input
  order.
- [x] **AC-21** A file that fails to convert does not stop the batch; the summary lists it with a human message
  and the technical detail; the exit code is 1.
- [x] **AC-22** A password-protected PDF fails with the code `password_protected` and the message "This PDF is
  password-protected. Remove the password and try again."; a corrupt file fails with `corrupt_file`.
- [x] **AC-23** A file that exceeds the time limit is stopped with `timed_out` (AC-44); the worker is replaced
  and the batch continues.
- [x] **AC-24** A worker that exceeds the memory limit is stopped; the file is stopped with `out_of_memory`
  (AC-44) and the batch continues with a new worker.
- [x] **AC-25** If the worker dies (e.g. a crash in native code), the file fails with `worker_crashed` and the
  batch continues with a new worker.
- [x] **AC-26** Cancelling (Ctrl+C) stops the current file **at once** by stopping the worker. No partial `.md`
  is left; files finished before remain, the rest are reported as cancelled, the summary is still written, and
  the exit code is 130.
- [x] **AC-27** If an output root cannot be written (permission denied), its files fail with
  `permission_denied` and the suggestion to choose another folder (`--output-root`); other output roots
  continue.

### Summary

- [x] **AC-28** Each output root gets `Resumen_ClearMD.md` (that name in every language), in the user's
  language. On top, the last batch: date, ClearMD version and totals; a **name table** mapping each source to
  its output, with the detected format and how it was detected; skipped items (reason); failed items (human
  message + technical detail); cancelled items.
- [x] **AC-29** At the bottom, a **history**: one line per earlier batch in that output root, newest first
  (date and totals), carried over from the previous summary. If the previous history cannot be read, it starts
  again and the summary says so.
- [x] **AC-30** The CLI ends with a summary: converted / skipped / failed counts and the output folder(s).

### Language and settings

- [x] **AC-31** Every CLI message and the summary are in English or Spanish. Resolution order: `--lang` →
  settings → English. argparse's own usage and error messages stay in English (ADR-0017).
- [x] **AC-32** Every catalog key exists in both languages, with the same placeholders.
- [x] **AC-33** A missing settings file means defaults. An unreadable or invalid one means defaults for the
  invalid values plus a one-line warning — never a crash.
- [x] **AC-34** CLI flags override settings for that run only.

### CLI contract

- [x] **AC-35** Exit codes: `0` every planned conversion succeeded (skips are not failures) · `1` at least one
  conversion failed or was stopped · `2` usage error or no valid input · `3` a decision is required but there is no
  interactive terminal · `130` cancelled. If a batch is cancelled after some failures, 130 wins.
- [x] **AC-36** `--open` opens the output folder(s) in the system file browser when the batch ends. The CLI
  never does it by default.
- [x] **AC-37** `--dry-run` shows the plan (including skips and existing outputs) and writes nothing.
- [x] **AC-38** Progress is shown per file (`[3/37] report.pdf`) on standard error; `--quiet` shows only the
  summary and errors.

### Privacy

- [x] **AC-39** No conversion opens a network connection (ADR-0005): the test suite makes any socket
  connection fail, and markitdown plugins are disabled.

### Time left and durations

- [x] **AC-40** From the second file on, the progress line adds the estimated time left for the batch
  (`[12/37] report.pdf · about 3 min left`). The estimate starts from the benchmark's speeds and is corrected
  after every file with the ratio between measured and estimated time of the files already converted.
- [x] **AC-41** The name table of `Resumen_ClearMD.md` shows how long each file took to convert.

### Warnings in the plan and stopped files

- [x] **AC-42** A file whose **estimated memory** (the worker's base memory + its size × the format's memory
  per MiB measured by the benchmark) exceeds the worker memory limit is skipped while planning, before anything
  is converted, as "too big to convert (it would need about 6.9 GB of memory; the limit is 4 GB)".
- [x] **AC-43** A file whose **estimated time** exceeds the time limit is **not** skipped: the plan carries a
  warning, shown before converting ("may take more than 10 minutes (about 15 min) and be stopped"), and the
  file is converted — last, because of the cost order.
- [x] **AC-44** A file stopped by the time or memory limit is reported as **stopped**, not as failed: the CLI
  line and the summary's "Stopped" section say how long it ran and roughly how far it got by the estimate
  ("stopped after 10:00, about 65% by the estimate"), and suggest splitting it into smaller files. The exit
  code is 1.

## Actors and data

- **Actors:** a user through the CLI. Feature 005 adds the presenter and the GUIs on the same backend.
- **Data:** user documents (read-only), the generated `.md` files and `Resumen_ClearMD.md` (inside
  `ClearMD_Output` only), the settings file (read-only in this feature). Nothing is stored anywhere else; nothing
  leaves the machine.

## Risks / open questions

- **markitdown's error details are internal:** mapping exceptions to `password_protected` / `corrupt_file`
  depends on what its converters raise. Verified with fixtures; anything unknown falls back to
  `conversion_failed`.
- **Worker start-up cost:** 0.7 s per batch (and after every replacement), measured by the benchmark.
- **Two magika models in the worker:** `MarkItDown()` always creates its own `Magika()`; the content detector
  keeps a second one. The benchmark measured no noticeable memory for it, so markitdown's private instance is
  not reused.
- **Limit values** come from `docs/benchmarks/001-conversion-limits.md`: PDF is the time bottleneck (~10
  pages/s), xlsx the memory one (~30 MiB at most under the 4 GiB limit). Real documents may differ from the
  synthetic ones; the time-left estimate corrects itself per batch.
- **argparse in English:** a known gap (ADR-0017).
- **Windows specifics** (hidden attribute, long paths, case-insensitive file system, spawn start method) are
  tested on Linux by simulation here and on a real Windows machine and runner in feature 006.
- **Conversion quality** (PDF tables, layout) comes from markitdown and pdfminer, not from ClearMD.

### Known limitations after the reviews of feature 001

Accepted for now, each with where it is addressed:

- **Windows has no hard memory cap yet.** POSIX workers run under `RLIMIT_AS`; on Windows a single huge
  allocation is caught only by the 0.1 s sampling. A Job Object with `ProcessMemoryLimit` comes in feature 006,
  with the Windows runner.
- **The worker is resource isolation, not a sandbox.** A parser exploit runs with the user's rights. Dependency
  hygiene (advisory check of `uv.lock`, hash-pinned PyInstaller builds) is part of feature 006.
- **Memory estimate of OOXML files with renamed parts.** The pre-check counts `.xml`-like entries; a file that
  names its main part otherwise gets a low estimate and is caught by the runtime limits instead.
- **No cap on the size of a converted Markdown.** Bounded in practice by the 250 MiB input limit.
- **Absolute paths can appear in a summary** (with `--output-root`, and inside technical details). Local file;
  worth knowing before sharing it.
