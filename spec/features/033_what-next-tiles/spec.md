# Feature 033 — "What Next?" as the three tools and one box for the files

## Goal

032's "What Next?" mixed two questions in three buttons: keep or clear the files, and go Home.
Going Home always kept them. The owner asked for the files' choice everywhere. The dialog
separates the two questions: what to do (a tool) and what happens to the files (one box).

## Acceptance criteria (what MUST be true)

- [x] **AC-01** "What Next?" offers the three tools as small tiles with the start screen's icons:
  the tool just used comes first as "<tool> Again", then the others in the start screen's
  order. One click opens step 1 of that tool.
- [x] **AC-02** One box, "Keep the files you chose", ticked by default, applies to any tile:
  ticked, the list stays; unticked, it starts empty. Cancel closes the dialog and Results stays.
- [x] **AC-03** The texts in English and Spanish, titles in Title Case.
- [x] **AC-04** The three windows show it the same way (tiles in a row, the box under them,
  Cancel at the foot) and their screenshots show it.
