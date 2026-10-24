# Feature 001 — Batch conversion: core + CLI

## Goal

A user points ClearMD at files and/or folders and gets Markdown files in a `ClearMD_Output` folder next to
them, plus a report — from the command line, on a core that every GUI will reuse unchanged.

## Scope

- **Includes:**
  - The core pipeline of ADR-0010: inputs → scan → detect → **plan** → confirm → **execute** → report.
  - Formats through the markitdown adapter (ADR-0004): PDF, docx, pptx, xlsx, HTML (full page), CSV, EPUB,
    Jupyter notebooks (`.ipynb`) and plain text (`.txt`).
  - Format detection by extension, and by content (`magika`) when the extension is missing or unknown.
  - Progress events and error codes for future interfaces (ADR-0013).
  - English and Spanish for every message and for the report (ADR-0012).
  - Reading the shared settings file (ADR-0012). The CLI never writes it.
  - The complete CLI.
- **Does not include:** `.tex`, `.odt` and HTML article mode (features 002–004); presenter, GUIs and the
  settings window (005+); executables and CI (006); ZIP archives, OCR and image extraction (out of scope).

## Definitions

- **Input:** a path the user passes (file or folder).
- **Output root:** `<parent>/ClearMD_Output`, where `<parent>` is the folder that contains the input file, or
  the parent of the input folder. `--output-root DIR` replaces `<parent>` with `DIR`.
- **Batch:** all inputs of one invocation.
- **Plan:** every planned conversion and every skipped item, computed **before writing anything**.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_001_*.py`).

### Inputs and scanning

- [ ] **AC-01** Given a supported file `D/report.pdf`, when it is converted, then `D/ClearMD_Output/report.md`
  exists, is UTF-8 with LF line endings, and contains the document's text.
- [ ] **AC-02** Given a folder `P/project/` with nested subfolders, when it is converted, then
  `P/ClearMD_Output/project/` mirrors its structure for every supported file, and no empty folder is created
  for subfolders without supported files.
- [ ] **AC-03** Given `--no-recursive` (or the setting `recursive = false`), only the files directly inside an
  input folder are converted.
- [ ] **AC-04** Given several inputs from different places, each result goes to the output root of its own
  input (AC-01, AC-02).
- [ ] **AC-05** Scanning never enters a folder named `ClearMD_Output` (any letter case), never follows
  symbolic links, and skips hidden files and folders (name starting with `.`, or the hidden attribute on
  Windows) and Office lock files (`~$*`). A skipped folder is reported once, not file by file.
- [ ] **AC-06** Given an input that does not exist, it is reported and the rest of the batch continues. Given
  inputs with nothing to convert (e.g. an empty folder), the CLI says so, exits with 0 and creates no
  `ClearMD_Output`.
- [ ] **AC-07** A file larger than 250 MiB is skipped with the reason "too large".
- [ ] **AC-08** `.md` / `.markdown` files are skipped as "already Markdown"; `.zip` files are skipped with
  "ZIP archives are not supported — extract them first".

### Detection

- [ ] **AC-09** Given a supported document without extension, or with an unknown one, it is detected by its
  content and converted; the report says "detected by content".
- [ ] **AC-10** Given an unsupported file, it is skipped as "unsupported format" and the batch continues.

### Output names

- [ ] **AC-11** Given two inputs of the same batch that would produce the same output path — compared
  **case-insensitively**, e.g. `report.pdf` and `Report.docx` in one folder — they produce `report (pdf).md`
  and `Report (docx).md`. No output of a batch overwrites another output of the same batch, and the result does
  not depend on the order of the inputs.
- [ ] **AC-12** The output keeps the full source stem: `report.v2.final.pdf` → `report.v2.final.md`; Unicode
  names (`informe_año_ñ.docx`) are preserved.
- [ ] **AC-13** A source that would produce `clearmd-report.md` gets the suffix of AC-11
  (`clearmd-report (docx).md`): that name is reserved for the report.

### Existing outputs

- [ ] **AC-14** Given outputs that already exist from a previous run, the plan marks them, and in an
  interactive terminal the CLI asks **once**: overwrite all, skip all, or decide one by one.
- [ ] **AC-15** `--overwrite` and `--skip` answer that question in advance; using both is a usage error.
- [ ] **AC-16** Given existing outputs, no interactive terminal, no flag and the setting
  `on_existing_output = "ask"`, nothing is written, the exit code is 3 and the message names the flags to use.
  If the setting is `overwrite` or `skip`, it is applied without asking.

### Execution and robustness

- [ ] **AC-17** A file that fails to convert does not stop the batch; the report lists it with a human message
  and the technical detail; the exit code is 1.
- [ ] **AC-18** A password-protected PDF fails with the code `password_protected` and the message "This PDF is
  password-protected. Remove the password and try again."; a corrupt file fails with `corrupt_file`.
- [ ] **AC-19** Outputs are written atomically: an interruption (Ctrl+C) never leaves a partial `.md`. Files
  finished before the interruption remain, the rest are reported as cancelled, the report is still written, and
  the exit code is 130.
- [ ] **AC-20** If an output root cannot be written (permission denied), its files are reported as failed with
  `permission_denied` and the suggestion to use `--output-root`; other output roots continue.
- [ ] **AC-21** `--output-root DIR` writes to `DIR/ClearMD_Output/` with the same relative layout
  (`name.md` for files, `<folder>/…` for folders).

### Report and summary

- [ ] **AC-22** Each output root gets `clearmd-report.md`, replaced on every batch, listing for that root:
  converted (source → output, detected format), skipped (reason), failed (human message + technical detail)
  and cancelled items, plus date, ClearMD version and totals, in the user's language.
- [ ] **AC-23** The CLI ends with a summary: converted / skipped / failed counts and the output folder(s).

### Language and settings

- [ ] **AC-24** Every CLI message and the report are in English or Spanish. Resolution order: `--lang` →
  settings → operating system locale → English.
- [ ] **AC-25** Every catalog key exists in both languages, with the same placeholders.
- [ ] **AC-26** A missing settings file means defaults. An unreadable or invalid one means defaults for the
  invalid values plus a one-line warning — never a crash.
- [ ] **AC-27** CLI flags override settings for that run only.

### CLI contract

- [ ] **AC-28** Exit codes: `0` every planned conversion succeeded (skips are not failures) · `1` at least one
  conversion failed · `2` usage error or no valid input · `3` a decision is required but there is no
  interactive terminal · `130` cancelled.
- [ ] **AC-29** `--open` opens the output folder(s) in the system file browser when the batch ends. The CLI
  never does it by default.
- [ ] **AC-30** `--dry-run` shows the plan and writes nothing.
- [ ] **AC-31** Progress is shown per file (`[3/37] report.pdf`) on standard error; `--quiet` shows only the
  summary and errors.

### Privacy

- [ ] **AC-32** No conversion opens a network connection (ADR-0005): the test suite makes any socket
  connection fail, and markitdown plugins are disabled.

## Actors and data

- **Actors:** a user through the CLI. Feature 005 adds the presenter and the GUIs on the same core.
- **Data:** user documents (read-only), the generated `.md` files and report (inside `ClearMD_Output` only),
  the settings file (read-only in this feature). Nothing is stored anywhere else; nothing leaves the machine.

## Risks / open questions

- **markitdown's error details are internal:** mapping exceptions to `password_protected` / `corrupt_file`
  depends on what its converters raise. Verified with fixtures; anything unknown falls back to
  `conversion_failed`.
- **magika's start-up cost:** its model loads on first use. It is only used for files without a known
  extension; the load time is measured and documented.
- **Windows specifics** (hidden attribute, long paths, case-insensitive file system) are tested on Linux by
  simulation here and on a real Windows runner in feature 006.
- **Conversion quality** (PDF tables, layout) comes from markitdown and pdfminer, not from ClearMD.
