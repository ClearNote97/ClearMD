# Feature 035 — Honest signals, a Help that guides, the full reason and the path (audit 4–7)

## Goal

The audit of 2.8.1 ([report](../../../docs/audit/2026-11-08-audit-boards.md)) found that the product
warns when all went well, hides the reason exactly where it says what to do, and never writes
where the files are. This feature closes recommendations 4 to 7 and the owner's decision 2C
(fill step 3 now; decide later whether to merge it with Review).

## Acceptance criteria (what MUST be true)

- [x] **AC-01** Notes have two levels. What ClearMD only tidied up (running headers removed, text
  decoded) is told in a calm section, "What ClearMD Tidied Up", without ⚠️ and outside the count
  of what needs attention; a clean PDF gives ✅. The command line no longer says "converted with
  notes" for those (B3-02).
- [x] **AC-02** Kept results are the user's choice, not a problem: they are not rows of "What
  Needs Your Attention", they have their own figure ("Kept"), their folders can be opened, and
  every count (window, summary, command line) tells them apart from what was left out (F1-03,
  F4-06).
- [x] **AC-03** Each row of Results opens with a word ("Failed:", "Stopped:", "Left out:") and has
  a tone of its own, so its kind never depends on colour alone (F3-03).
- [x] **AC-04** Help is the same in the three windows and describes the real product: what
  Markdown is, the real flow with the buttons' real names, the three tools and their folders,
  what is not converted (images, scans, old Office files); dropping is mentioned only when the
  window can take dropped files (F4-02, F4-01, F1-04).
- [x] **AC-05** Review shows the full reason and what to do for the selected row, below the list,
  with the first row that has a problem selected at first; no explanation is cut without another
  way to read it (F3-01, F4-04).
- [x] **AC-06** Results says where the files are, as text the user can read and copy, with the
  tool's folder (OutputMD, OutputSep or OutputUnif) (F3-11, F4-03).
- [x] **AC-07** The classic (ttk) window's list shows its scroll bar whenever rows are hidden, and
  shows a thousand rows without freezing (F2-01, F3-02).
- [x] **AC-08** Step 3 says how many files will really be written and what happens to the results
  that already exist, as decided; the Welcome no longer counts steps the window does not have;
  the summary says where the files are only when there are files (2C, F4-08, B4-04).
- [x] **AC-09** The texts in English and Spanish, titles in Title Case.
