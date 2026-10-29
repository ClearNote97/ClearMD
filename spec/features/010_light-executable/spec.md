# Feature 010 — A light executable

## Goal

The executable weighed about 90 MB for a few small jobs done by large libraries. It must be much
lighter, and convert the same (ADR-0032).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_010_light_executable.py`).

- [ ] **AC-01** A file without an extension is recognised by its content, by ClearMD's own
  signatures, for every format ClearMD converts; a program or unknown data is "unsupported".
- [ ] **AC-02** Excel workbooks are converted by ClearMD's own converter: each sheet a heading
  and a table, as before, every cell escaped; an encrypted workbook is "password-protected".
- [ ] **AC-03** The executables leave out magika, onnxruntime, numpy and pandas, keep only
  babel's root, English and Spanish data, and their notices list only what ships.
- [ ] **AC-04** The executables still convert the real batch of every format (the same check as
  feature 006), and the Linux one is under 50 MB.
