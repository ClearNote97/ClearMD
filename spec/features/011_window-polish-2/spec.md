# Feature 011 — Window polish II

## Goal

What the author asked for after using v0.5.0: Settings and Help as sections of the rail, the
decorative shape never cut by the page, and the line next to the action buttons saying on every
page what is missing (ADR-0027, ADR-0029).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_011_window_polish_2.py`).

- [x] **AC-01** Settings and Help are as wide and as tall as a step, their mark where a step has
  its number; in the compact rail, their marks alone, centred.
- [x] **AC-02** The shape at the top right is whole within the header; the page is outlined as a
  soft card that follows a resize at once, with a margin at its sides; at the smallest window
  (800 × 600 now; a short window puts Choose's add buttons side by side) the lists keep rows.
- [x] **AC-03** With nothing chosen, every page's hint says to add files or folders on Choose;
  with files chosen and no plan, Review and Convert say to press Next on Choose; after a batch
  that wrote nothing, Results says so; a long hint takes two lines, never cut.
- [x] **AC-04** Everything new follows ADR-0027, in English and Spanish, and has screenshots in
  `docs/screenshots/011/`.
