# Feature 036 — Clear messages, a kind first run, progress and estimates (audit 8–10, decision 3B)

## Goal

The audit of 2.8.1 ([report](../../../docs/audit/2026-11-08-audit-boards.md)) found messages that
guess a wrong cause or speak the terminal's language in the window, a first run that downloads
five times what it installs and opens in English after a Spanish installer, long files that show
no progress and are lost after ten minutes, and Excel splits estimated as PDFs. This feature
closes recommendations 8 to 10 and the owner's decision 3B: show "page N of M" and stop a file
only when it stops moving.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** The window's texts carry no command-line options, no library names and no scary
  words ("zip bomb", "symbolic link"); the terminal says its own options in place of the
  window's buttons (`Catalog.for_terminal`) (F4-07, B4-05, B4-06).
- [x] **AC-02** A message never guesses: an encrypted Word or PowerPoint file is "protected with
  a password", not "damaged"; an empty file is "empty", not "scanned"; "could not save" says to
  close the result if another program has it open; "could not convert" says what to do (B1-07,
  B4-02).
- [x] **AC-03** Old Word, Excel and PowerPoint files (.doc, .xls, .ppt) and pictures are left out
  with a reason and a way forward of their own (C-2).
- [x] **AC-04** The unexpected error no longer shows an exception's name: it reassures and says
  where to tell (the issues page); a "Copy Details" button copies the version, the window, the
  system and the error with every path replaced by `<file>.ext` (F4-05, F1-07, doubts board D3).
- [x] **AC-05** A PDF being converted reports "Page N of M" to the window; the time limit counts
  from the last progress, so a long file that keeps moving finishes and a stuck one stops (with
  a ceiling of six times the limit) (3B, B2-04).
- [x] **AC-06** Splitting an Excel workbook is estimated as Excel (one load per part) and is
  checked against the worker's memory before it starts (B2-01).
- [x] **AC-07** A kind first run: the app opens in the installer's language on a first install
  (an existing settings file is never touched); components, shortcuts and cards are named by
  what a person notices (Classic App, Modern App, Mobile-Style App, Command Line), with the
  technology as secondary text, and the shortcuts of every earlier name are removed (C-1, B4-09,
  doubts board D2). The light installer is feature 037 (one risk per version, doubts board D1).
- [x] **AC-08** The texts in English and Spanish.
