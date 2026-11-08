# Feature 032 — Merge's order, "What Next?", and the start screen alike in the three windows

## Goal

What the owner found testing 2.7.0:

- Merge joins the documents in the list's order, but the list had no way to change it.
- Results only offered to do the same again ("Convert More"); going back to the start screen to
  use another tool meant finding Home in the rail.
- The Welcome still spoke of converting only, flet's start screen did not centre its tiles, the
  tiles' icons were not the same in the three windows, and some details differed between them.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** In Merge, each document of step 1's list can be moved one place up or down; the
  merge follows the new order. The first cannot go up and the last cannot go down; Convert and
  Split do not offer it (their order does not change the result). Moving a document drops a plan
  made with the earlier order.
- [x] **AC-02** On Results, the second button is "What Next?" in the three tools. It asks once:
  keep the files, start empty, or go back Home to choose another tool. Going Home keeps the files.
- [x] **AC-03** The Welcome speaks of the three tools, in English and Spanish.
- [x] **AC-04** The three windows draw the start screen alike: the three tiles centred in the page,
  with the same icons (the app's own pictures, not each toolkit's).
- [x] **AC-05** The three windows show the order buttons (AC-01) and "What Next?" (AC-02); no
  button looks pressed or focused when a page opens.
