# Feature 007 — Navigation and window polish

## Goal

What the author asked for after using v0.1.0: move freely between the steps, always know why a
button is disabled, select files comfortably, a window that resizes smoothly, and a start that
shows it is loading.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_007_navigation_and_polish.py`).

### Navigation (ADR-0029)
- [x] **AC-01** Every step of the rail can be opened at any time (click or keyboard); the page on
  screen is highlighted, the other steps are dimmed, each number in a smooth circle.
- [x] **AC-02** The primary action is **Next** on Choose and Review, **Convert** on Convert, **Open
  results folder** on Results; when it cannot run it is disabled and one line says why.
- [x] **AC-03** Next on Choose plans the batch and opens Review; Next on Review opens Convert;
  Convert starts the batch on that page, shows its progress there and opens Results at the end.
- [x] **AC-04** Changing the inputs or the output after a plan drops it (Review says to press Next
  on Choose); nothing can be edited while analyzing or converting.
- [x] **AC-05** On Results both actions are prominent; **Convert more** asks every time whether to
  keep the chosen files, and goes back to Choose with them or without them.

### Lists
- [x] **AC-06** Every list shows a checkbox before the number, checked when the row is selected;
  the header's checkbox selects or clears all; **Clear selection** clears it; a click on an empty
  part of the list clears it too.
- [x] **AC-07** The column headings show faint separators where a column can be resized.
- [x] **AC-08** On Review, a file without problems says **✓ Ready to convert**; the others say why
  not, as before.

### The window
- [x] **AC-09** Resizing redraws the backgrounds once the size settles (not on every pixel); the
  window can shrink to 800 × 560 (600 since feature 011), and below 1000 px wide the rail is compact (logo and numbers).
- [x] **AC-10** The version is on screen (the rail's footer) and in the help.
- [x] **AC-11** The executable's splash shows the logo, *Turn your documents into Markdown*, and
  "Loading · Cargando… N %" (it starts before any setting is read: both languages) moving through the real stages of the start.
- [x] **AC-12** Everything new follows ADR-0027 (palette, type, 8 px grid, WCAG AA), in English
  and Spanish, works with the keyboard, and has screenshots in `docs/screenshots/007/`.
