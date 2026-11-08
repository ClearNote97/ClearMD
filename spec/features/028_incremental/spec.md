# Feature 028 — Incremental mode: only what changed

## Goal

When a folder is converted again, the files that have not changed since their result was written
should be skipped, and only the new or edited ones converted. The setting "When a Result Already
Exists" gains a fourth choice, **Replace it if the original changed** (ADR-0048). No database is
needed: an original newer than its result has changed since that result was written.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** With "Replace it if the original changed":
  - a result whose original was modified after the result was written is converted again;
  - a result whose original is older is kept and said so ("unchanged since its result");
  - a file without a result is converted as always.
- [x] **AC-02** It works the same way for Split: an existing parts folder whose original is
  newer is split again, and an older one is kept. Merge always writes a new file, so this does
  not apply to it.
- [x] **AC-03** The command line takes `--changed`. It cannot go with `--overwrite` or `--skip`.
  The setting's value is `changed`.
- [x] **AC-04** The three windows offer the choice in Settings, and on Review when results
  already exist (next to Replace and Keep). The summary counts the files that were unchanged and
  kept.
- [x] **AC-05** Texts in English and Spanish.
